from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.batch import Batch
from app.models.inventory_movement import InventoryMovement
from app.models.role import Role
from app.models.sale import Sale
from app.models.user import User

FIXTURE_PASSWORD = "FixturePass123!"


def _login(client, email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _ensure_user(db: Session, role_name: str, email: str, username: str) -> User:
    existing = db.scalar(select(User).where(User.email == email))
    if existing is not None:
        return existing

    role = db.scalar(select(Role).where(Role.name == role_name))
    assert role is not None

    user = User(
        full_name=f"Sales {role_name.title()}",
        email=email,
        username=username,
        password_hash=hash_password(FIXTURE_PASSWORD),
        role_id=role.id,
        status="active",
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture
def owner_headers(client):
    return _login(client, settings.demo_email, settings.demo_password)


@pytest.fixture
def staff_headers(client, db_session: Session):
    _ensure_user(db_session, "staff", "sales.staff@aetherqore.local", "salesstaff")
    return _login(client, "sales.staff@aetherqore.local", FIXTURE_PASSWORD)


def _create_medicine(client, headers) -> dict:
    suffix = uuid4().hex[:8]
    response = client.post(
        "/api/medicines",
        headers=headers,
        json={
            "name": f"Sale Medicine {suffix}",
            "generic_name": "Test Generic",
            "dosage_form": "Tablet",
            "strength": "500mg",
            "barcode": f"SALE{suffix.upper()}",
        },
    )
    assert response.status_code == 201, response.json()
    return response.json()["data"]


def _create_batch(client, headers, medicine_id: int, **overrides) -> dict:
    payload = {
        "medicine_id": medicine_id,
        "batch_number": f"SALE-{uuid4().hex[:6].upper()}",
        "expiry_date": (date.today() + timedelta(days=180)).isoformat(),
        "cost_price": 5.0,
        "selling_price": 10.0,
        "quantity_received": 50,
    }
    payload.update(overrides)
    response = client.post("/api/batches", headers=headers, json=payload)
    assert response.status_code == 201, response.json()
    return response.json()["data"]


def test_create_sale_requires_auth(client, owner_headers):
    medicine = _create_medicine(client, owner_headers)
    _create_batch(client, owner_headers, medicine["id"])

    response = client.post(
        "/api/sales",
        json={
            "payment_method": "cash",
            "lines": [{"medicine_id": medicine["id"], "quantity": 1}],
        },
    )
    assert response.status_code == 401
    assert response.json()["message"] == "Authentication required"


def test_staff_sale_decrements_batch_and_creates_stock_out(
    client,
    staff_headers,
    owner_headers,
    db_session: Session,
):
    medicine = _create_medicine(client, owner_headers)
    batch = _create_batch(
        client,
        owner_headers,
        medicine["id"],
        quantity_received=20,
        selling_price=12.5,
    )

    response = client.post(
        "/api/sales",
        headers=staff_headers,
        json={
            "payment_method": "momo",
            "lines": [{"medicine_id": medicine["id"], "quantity": 3}],
        },
    )
    assert response.status_code == 201, response.json()
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert Decimal(str(data["total"])) == Decimal("37.50")
    assert len(data["lines"]) == 1
    assert data["lines"][0]["batch_id"] == batch["id"]
    assert data["lines"][0]["quantity"] == 3

    refreshed = db_session.get(Batch, batch["id"])
    assert refreshed is not None
    assert refreshed.quantity_on_hand == 17

    movements = list(
        db_session.scalars(
            select(InventoryMovement).where(
                InventoryMovement.reference_type == "sale",
                InventoryMovement.batch_id == batch["id"],
            )
        )
    )
    assert len(movements) == 1
    assert movements[0].movement_type == "stock_out"
    assert movements[0].quantity_change == -3


def test_fefo_consumes_earlier_expiry_first(
    client,
    owner_headers,
    db_session: Session,
):
    medicine = _create_medicine(client, owner_headers)
    later = _create_batch(
        client,
        owner_headers,
        medicine["id"],
        batch_number="LATER-EXP",
        expiry_date=(date.today() + timedelta(days=365)).isoformat(),
        selling_price=20.0,
        quantity_received=10,
    )
    sooner = _create_batch(
        client,
        owner_headers,
        medicine["id"],
        batch_number="SOON-EXP",
        expiry_date=(date.today() + timedelta(days=30)).isoformat(),
        selling_price=15.0,
        quantity_received=10,
    )

    response = client.post(
        "/api/sales",
        headers=owner_headers,
        json={
            "payment_method": "cash",
            "lines": [{"medicine_id": medicine["id"], "quantity": 5}],
        },
    )
    assert response.status_code == 201, response.json()
    lines = response.json()["data"]["lines"]
    assert len(lines) == 1
    assert lines[0]["batch_id"] == sooner["id"]
    assert lines[0]["unit_price"] == "15.00"

    assert db_session.get(Batch, sooner["id"]).quantity_on_hand == 5
    assert db_session.get(Batch, later["id"]).quantity_on_hand == 10


def test_fefo_splits_across_batches(client, owner_headers, db_session: Session):
    medicine = _create_medicine(client, owner_headers)
    first = _create_batch(
        client,
        owner_headers,
        medicine["id"],
        batch_number="FEFO-A",
        expiry_date=(date.today() + timedelta(days=60)).isoformat(),
        quantity_received=3,
        selling_price=10.0,
    )
    second = _create_batch(
        client,
        owner_headers,
        medicine["id"],
        batch_number="FEFO-B",
        expiry_date=(date.today() + timedelta(days=120)).isoformat(),
        quantity_received=10,
        selling_price=10.0,
    )

    response = client.post(
        "/api/sales",
        headers=owner_headers,
        json={
            "payment_method": "card",
            "lines": [{"medicine_id": medicine["id"], "quantity": 5}],
        },
    )
    assert response.status_code == 201, response.json()
    lines = response.json()["data"]["lines"]
    assert len(lines) == 2
    by_batch = {line["batch_id"]: line["quantity"] for line in lines}
    assert by_batch[first["id"]] == 3
    assert by_batch[second["id"]] == 2


def test_insufficient_stock_returns_409_without_side_effects(
    client,
    owner_headers,
    db_session: Session,
):
    medicine = _create_medicine(client, owner_headers)
    batch = _create_batch(
        client,
        owner_headers,
        medicine["id"],
        quantity_received=2,
    )

    sales_before = db_session.scalar(select(func.count()).select_from(Sale))
    movements_before = db_session.scalar(select(func.count()).select_from(InventoryMovement))

    response = client.post(
        "/api/sales",
        headers=owner_headers,
        json={
            "payment_method": "cash",
            "lines": [{"medicine_id": medicine["id"], "quantity": 5}],
        },
    )
    assert response.status_code == 409
    assert response.json()["message"] == "Insufficient stock to complete sale"

    sales_after = db_session.scalar(select(func.count()).select_from(Sale))
    movements_after = db_session.scalar(select(func.count()).select_from(InventoryMovement))
    assert sales_after == sales_before
    assert movements_after == movements_before
    assert db_session.get(Batch, batch["id"]).quantity_on_hand == 2


def test_expired_batch_is_not_sold_from(client, owner_headers, db_session: Session):
    medicine = _create_medicine(client, owner_headers)
    expired = _create_batch(
        client,
        owner_headers,
        medicine["id"],
        batch_number="EXPIRED-ONLY",
        expiry_date=(date.today() - timedelta(days=1)).isoformat(),
        quantity_received=20,
    )
    good = _create_batch(
        client,
        owner_headers,
        medicine["id"],
        batch_number="GOOD-STOCK",
        expiry_date=(date.today() + timedelta(days=90)).isoformat(),
        quantity_received=5,
        selling_price=8.0,
    )

    response = client.post(
        "/api/sales",
        headers=owner_headers,
        json={
            "payment_method": "cash",
            "lines": [{"medicine_id": medicine["id"], "quantity": 2}],
        },
    )
    assert response.status_code == 201, response.json()
    assert response.json()["data"]["lines"][0]["batch_id"] == good["id"]
    assert db_session.get(Batch, expired["id"]).quantity_on_hand == 20


def test_dashboard_today_sales_includes_new_sale(client, owner_headers):
    medicine = _create_medicine(client, owner_headers)
    _create_batch(
        client,
        owner_headers,
        medicine["id"],
        quantity_received=10,
        selling_price=25.0,
    )

    before = client.get("/api/dashboard/summary", headers=owner_headers)
    assert before.status_code == 200
    amount_before = before.json()["data"]["today_sales"]["amount"]

    sale = client.post(
        "/api/sales",
        headers=owner_headers,
        json={
            "payment_method": "cash",
            "lines": [{"medicine_id": medicine["id"], "quantity": 2}],
        },
    )
    assert sale.status_code == 201

    after = client.get("/api/dashboard/summary", headers=owner_headers)
    assert after.status_code == 200
    amount_after = after.json()["data"]["today_sales"]["amount"]
    assert amount_after == pytest.approx(amount_before + 50.0)
    assert after.json()["data"]["today_sales"]["currency"] == "GHS"
