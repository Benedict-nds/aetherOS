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
