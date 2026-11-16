from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.batch import Batch
from app.models.medicine import Medicine
from app.models.role import Role
from app.models.user import User


def _login(client, email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def owner_headers(client):
    return _login(client, settings.demo_email, settings.demo_password)


@pytest.fixture
def staff_headers(client, db_session: Session):
    role = db_session.scalar(select(Role).where(Role.name == "staff"))
    assert role is not None
    email = "staff.reports@aetherqore.local"
    user = db_session.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            full_name="Staff Reports User",
            email=email,
            username="staffreports",
            password_hash=hash_password("StaffPass123!"),
            role_id=role.id,
            status="active",
        )
        db_session.add(user)
        db_session.commit()
    return _login(client, email, "StaffPass123!")


def _get_medicine_by_barcode(db_session: Session, barcode: str) -> Medicine:
    medicine = db_session.scalar(select(Medicine).where(Medicine.barcode == barcode))
    assert medicine is not None
    return medicine


def _add_batch(
    db_session: Session,
    *,
    medicine: Medicine,
    batch_number: str,
    expiry_date: date | None,
    quantity_on_hand: int,
) -> Batch:
    batch = Batch(
        medicine_id=medicine.id,
        batch_number=batch_number,
        expiry_date=expiry_date,
        cost_price=Decimal("10.00"),
        selling_price=Decimal("15.00"),
        quantity_on_hand=quantity_on_hand,
        quantity_received=quantity_on_hand,
        status="active",
    )
    db_session.add(batch)
    db_session.commit()
    return batch


def test_unauthenticated_low_stock_returns_401(client):
    response = client.get("/api/reports/low-stock")
    assert response.status_code == 401


def test_low_stock_includes_never_stocked_medicine(client, owner_headers, db_session):
    for batch in db_session.scalars(select(Batch)).all():
        db_session.delete(batch)
    db_session.commit()

    medicine = _get_medicine_by_barcode(db_session, "MET500001")
    assert medicine.reorder_level > 0

    response = client.get("/api/reports/low-stock", headers=owner_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True

    match = next(row for row in body["data"] if row["medicine_id"] == medicine.id)
    assert match["name"] == medicine.name
    assert match["quantity_on_hand"] == 0
    assert match["reorder_level"] == medicine.reorder_level

    dashboard = client.get("/api/dashboard/summary", headers=owner_headers)
    assert dashboard.status_code == 200
    data = dashboard.json()["data"]
    assert data["low_stock_count"] >= 1
    assert data["expiring_soon_count"] == 0
    assert data["today_sales"] == {"amount": 0, "currency": "GHS"}
    assert data["open_orders_count"] == 0


def test_low_stock_includes_medicine_below_reorder_level(
    client,
    owner_headers,
    db_session,
):
    medicine = _get_medicine_by_barcode(db_session, "MET500001")
    _add_batch(
        db_session,
        medicine=medicine,
        batch_number="MET-TEST-001",
        expiry_date=date.today() + timedelta(days=180),
        quantity_on_hand=5,
    )

    response = client.get("/api/reports/low-stock", headers=owner_headers)
    assert response.status_code == 200
    rows = response.json()["data"]
    match = next(row for row in rows if row["medicine_id"] == medicine.id)
    assert match["name"] == medicine.name
    assert match["quantity_on_hand"] == 5
    assert match["reorder_level"] == medicine.reorder_level

    dashboard = client.get("/api/dashboard/summary", headers=owner_headers)
    assert dashboard.json()["data"]["low_stock_count"] >= 1


def test_expiry_report_marks_expired_and_30_day_buckets(
    client,
    owner_headers,
    db_session,
):
    medicine = _get_medicine_by_barcode(db_session, "AMOX500001")
    expired_batch = _add_batch(
        db_session,
        medicine=medicine,
        batch_number="AMX-EXPIRED",
        expiry_date=date.today() - timedelta(days=1),
        quantity_on_hand=100,
    )
    soon_batch = _add_batch(
        db_session,
        medicine=medicine,
        batch_number="AMX-SOON",
        expiry_date=date.today() + timedelta(days=10),
        quantity_on_hand=50,
    )

    response = client.get("/api/reports/expiry", headers=owner_headers)
    assert response.status_code == 200
    rows = response.json()["data"]

    expired_row = next(row for row in rows if row["batch_id"] == expired_batch.id)
    assert expired_row["bucket"] == "expired"
    assert expired_row["expiry_date"] == expired_batch.expiry_date.isoformat()

    soon_row = next(row for row in rows if row["batch_id"] == soon_batch.id)
    assert soon_row["bucket"] == "30"


def test_staff_can_read_reports(client, staff_headers, db_session):
    medicine = _get_medicine_by_barcode(db_session, "LIS10001")
    _add_batch(
        db_session,
        medicine=medicine,
        batch_number="LIS-STAFF-001",
        expiry_date=date.today() + timedelta(days=5),
        quantity_on_hand=3,
    )

    low_stock = client.get("/api/reports/low-stock", headers=staff_headers)
    assert low_stock.status_code == 200

    expiry = client.get("/api/reports/expiry", headers=staff_headers)
    assert expiry.status_code == 200


@pytest.fixture
def report_db(client):
    from app.core.db import engine, get_db
    from app.main import app
    with engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        app.dependency_overrides[get_db] = lambda: session
        try:
            yield session
        finally:
            app.dependency_overrides.pop(get_db, None)
            session.close()
            transaction.rollback()


def _report_user(db, role_name):
    from uuid import uuid4
    suffix = uuid4().hex
    role = db.scalar(select(Role).where(Role.name == role_name))
    user = User(full_name=f"Report {role_name}", email=f"{suffix}@reports.local",
                username=suffix, password_hash=hash_password("ReportPass123!"),
                role_id=role.id, status="active")
    db.add(user)
    db.flush()
    return user


def test_daily_sales_breakdowns_and_utc_boundaries(client, owner_headers, report_db):
    from datetime import datetime, timezone
    from app.models.sale import Sale
    from app.models.sale_line import SaleLine
    db = report_db
    users = [_report_user(db, role) for role in ("pharmacist", "staff")]
    medicines = [_get_medicine_by_barcode(db, code) for code in ("AMOX500001", "PARA500001")]
    batches = [_add_batch(db, medicine=med, batch_number=f"REPORT-{i}", expiry_date=None,
                          quantity_on_hand=10) for i, med in enumerate(medicines)]
    for timestamp, method, user, lines in [
        (datetime(2040, 10, 20, tzinfo=timezone.utc), "cash", users[0], [(0, 2, "10.25"), (1, 1, "3.10")]),
        (datetime(2040, 10, 20, 23, 59, 59, 999999, tzinfo=timezone.utc), "momo", users[1], [(0, 3, "10.25")]),
        (datetime(2040, 10, 19, 23, 59, 59, tzinfo=timezone.utc), "cash", users[1], [(0, 1, "99.00")]),
        (datetime(2040, 10, 21, tzinfo=timezone.utc), "cash", users[1], [(0, 1, "99.00")]),
    ]:
        sale = Sale(payment_method=method, user_id=user.id, created_at=timestamp,
                    total=sum(Decimal(price) * qty for _, qty, price in lines))
        db.add(sale)
        db.flush()
        for i, qty, price in lines:
            db.add(SaleLine(sale_id=sale.id, batch_id=batches[i].id,
                            medicine_id=medicines[i].id, quantity=qty, unit_price=Decimal(price)))
    db.commit()
    response = client.get("/api/reports/daily-sales?date=2040-10-20", headers=owner_headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    data = response.json()["data"]
    assert (data["date"], data["currency"], data["total_amount"], data["sale_count"]) == ("2040-10-20", "GHS", 54.35, 2)
    assert data["by_payment_method"] == [
        {"payment_method": "cash", "sale_count": 1, "amount": 23.6},
        {"payment_method": "momo", "sale_count": 1, "amount": 30.75}]
    assert data["by_cashier"] == [
        {"user_id": user.id, "full_name": user.full_name, "sale_count": 1, "amount": amount}
        for user, amount in zip(users, [23.6, 30.75])]
    assert data["by_category"] == [
        {"category_id": medicines[0].category_id, "category_name": medicines[0].category.name, "quantity": 5, "amount": 51.25},
        {"category_id": None, "category_name": None, "quantity": 1, "amount": 3.1}]


def test_daily_sales_empty_date(client, owner_headers):
    response = client.get("/api/reports/daily-sales?date=2099-01-01", headers=owner_headers)
    assert response.status_code == 200
    assert response.json()["data"] == {
        "date": "2099-01-01", "currency": "GHS", "total_amount": 0, "sale_count": 0,
        "by_payment_method": [], "by_cashier": [], "by_category": []}


def test_daily_sales_defaults_to_utc_date(client, owner_headers):
    from datetime import datetime, timezone
    from unittest.mock import patch
    with patch("app.modules.reports.service.datetime") as clock:
        clock.now.return_value = datetime(2098, 6, 2, 0, 1, tzinfo=timezone.utc)
        response = client.get("/api/reports/daily-sales", headers=owner_headers)
        clock.now.assert_called_once_with(timezone.utc)
    assert response.status_code == 200
    assert response.json()["data"]["date"] == "2098-06-02"


def test_daily_sales_invalid_date(client, owner_headers):
    assert client.get("/api/reports/daily-sales?date=invalid", headers=owner_headers).status_code == 422


def test_inventory_valuation_filters_and_decimal_totals(client, owner_headers, report_db):
    from uuid import uuid4
    db = report_db
    medicines = [Medicine(name=f"Valuation {uuid4().hex}") for _ in range(2)]
    db.add_all(medicines)
    db.flush()
    for medicine, qty, cost, retail, status in [
        (medicines[0], 3, "0.10", "0.30", "active"),
        (medicines[0], 2, "1.25", "2.35", "expired"),
        (medicines[1], 4, "2.50", "4.00", "active"),
        (medicines[0], 100, "999.00", "999.00", "void"),
        (medicines[1], 0, "999.00", "999.00", "active"),
    ]:
        db.add(Batch(medicine_id=medicine.id, batch_number=uuid4().hex,
                     quantity_on_hand=qty, quantity_received=qty, cost_price=Decimal(cost),
                     selling_price=Decimal(retail), status=status))
    db.commit()
    response = client.get("/api/reports/inventory-valuation", headers=owner_headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["currency"] == "GHS"
    rows = {row["medicine_id"]: row for row in data["rows"]}
    assert rows[medicines[0].id] == {
        "medicine_id": medicines[0].id, "name": medicines[0].name, "category_name": None,
        "quantity_on_hand": 5, "cost_value": 2.8, "retail_value": 5.6}
    assert rows[medicines[1].id]["cost_value"] == 10
    assert rows[medicines[1].id]["retail_value"] == 16
    assert rows[medicines[1].id]["quantity_on_hand"] == 4
    for total, field in [("total_cost_value", "cost_value"), ("total_retail_value", "retail_value")]:
        assert Decimal(str(data[total])) == sum(Decimal(str(row[field])) for row in data["rows"])
    costs = [row["cost_value"] for row in data["rows"]]
    assert costs == sorted(costs, reverse=True)


@pytest.mark.parametrize("role,daily_status,valuation_status", [
    ("owner", 200, 200), ("admin", 200, 200), ("pharmacist", 200, 403), ("staff", 403, 403)])
def test_new_report_roles(client, report_db, role, daily_status, valuation_status):
    user = _report_user(report_db, role)
    report_db.commit()
    headers = _login(client, user.email, "ReportPass123!")
    assert client.get("/api/reports/daily-sales", headers=headers).status_code == daily_status
    assert client.get("/api/reports/inventory-valuation", headers=headers).status_code == valuation_status


@pytest.mark.parametrize("endpoint", ["daily-sales", "inventory-valuation"])
def test_new_reports_require_authentication(client, endpoint):
    assert client.get(f"/api/reports/{endpoint}").status_code == 401
