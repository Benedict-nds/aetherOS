from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.batch import Batch
from app.models.inventory_movement import InventoryMovement
from app.models.refund_item import RefundItem
from app.models.role import Role
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
        full_name=f"Refund {role_name.title()}",
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
def pharmacist_headers(client, db_session: Session):
    _ensure_user(
        db_session,
        "pharmacist",
        "refunds.pharmacist@aetherqore.local",
        "refundspharmacist",
    )
    return _login(client, "refunds.pharmacist@aetherqore.local", FIXTURE_PASSWORD)


@pytest.fixture
def staff_headers(client, db_session: Session):
    _ensure_user(db_session, "staff", "refunds.staff@aetherqore.local", "refundsstaff")
    return _login(client, "refunds.staff@aetherqore.local", FIXTURE_PASSWORD)


def _create_medicine(client, headers) -> dict:
    suffix = uuid4().hex[:8]
    response = client.post(
        "/api/medicines",
        headers=headers,
        json={
            "name": f"Refund Medicine {suffix}",
            "generic_name": "Refund Generic",
            "dosage_form": "Tablet",
            "strength": "500mg",
            "barcode": f"RFD{suffix.upper()}",
        },
    )
    assert response.status_code == 201, response.json()
    return response.json()["data"]


def _create_batch(client, headers, medicine_id: int, **overrides) -> dict:
    payload = {
        "medicine_id": medicine_id,
        "batch_number": f"RFD-{uuid4().hex[:6].upper()}",
        "expiry_date": (date.today() + timedelta(days=180)).isoformat(),
        "cost_price": 5.0,
        "selling_price": 18.0,
        "quantity_received": 20,
    }
    payload.update(overrides)
    response = client.post("/api/batches", headers=headers, json=payload)
    assert response.status_code == 201, response.json()
    return response.json()["data"]


def _create_sale(client, headers, medicine_id: int, quantity: int) -> dict:
    response = client.post(
        "/api/sales",
        headers=headers,
        json={
            "payment_method": "cash",
            "lines": [{"medicine_id": medicine_id, "quantity": quantity}],
        },
    )
    assert response.status_code == 201, response.json()
    return response.json()["data"]


def test_full_line_refund_returns_stock_and_creates_movement_and_audit(
    client,
    owner_headers,
    pharmacist_headers,
    db_session: Session,
):
    medicine = _create_medicine(client, owner_headers)
    batch = _create_batch(client, owner_headers, medicine["id"], quantity_received=10, selling_price=18.0)
    sale = _create_sale(client, owner_headers, medicine["id"], quantity=2)
    sale_line = sale["lines"][0]

    before_batch = db_session.get(Batch, batch["id"])
    assert before_batch is not None
    assert before_batch.quantity_on_hand == 8

    response = client.post(
        "/api/refunds",
        headers=pharmacist_headers,
        json={
            "sale_id": sale["id"],
            "reason": "Customer returned unopened pack",
            "refund_method": "cash",
            "lines": [
                {
                    "sale_line_id": sale_line["id"],
                    "quantity": 2,
                    "return_to_stock": True,
                }
            ],
        },
    )
    assert response.status_code == 201, response.json()
    data = response.json()["data"]
    assert data["sale_id"] == sale["id"]
    assert data["refund_method"] == "cash"
    assert Decimal(str(data["total_amount"])) == Decimal("36.00")
    assert data["lines"][0]["batch_id"] == batch["id"]
    assert data["lines"][0]["return_to_stock"] is True

    refreshed = db_session.get(Batch, batch["id"])
    assert refreshed is not None
    assert refreshed.quantity_on_hand == 10

    refund_id = data["id"]
    movements = list(
        db_session.scalars(
            select(InventoryMovement).where(
                InventoryMovement.reference_type == "refund",
                InventoryMovement.reference_id == refund_id,
            )
        )
    )
    assert len(movements) == 1
    assert movements[0].quantity_change == 2
    assert movements[0].movement_type == "refund"

    audit = db_session.scalar(
        select(AuditLog)
        .where(
            AuditLog.entity_type == "refund",
            AuditLog.entity_id == refund_id,
            AuditLog.action == "refund.created",
        )
        .order_by(AuditLog.id.desc())
    )
    assert audit is not None
    assert audit.details is not None
    assert audit.details["sale_id"] == sale["id"]
    assert audit.details["line_count"] == 1
    assert audit.details["refund_method"] == "cash"


def test_partial_then_over_refund_returns_422(client, owner_headers, db_session: Session):
    medicine = _create_medicine(client, owner_headers)
    _create_batch(client, owner_headers, medicine["id"], quantity_received=10, selling_price=12.0)
    sale = _create_sale(client, owner_headers, medicine["id"], quantity=3)
    sale_line = sale["lines"][0]

    first = client.post(
        "/api/refunds",
        headers=owner_headers,
        json={
            "sale_id": sale["id"],
            "reason": "Partial return",
            "refund_method": "card",
            "lines": [
                {
                    "sale_line_id": sale_line["id"],
                    "quantity": 2,
                    "return_to_stock": True,
                }
            ],
        },
    )
    assert first.status_code == 201, first.json()

    second = client.post(
        "/api/refunds",
        headers=owner_headers,
        json={
            "sale_id": sale["id"],
            "reason": "Second return too much",
            "refund_method": "card",
            "lines": [
                {
                    "sale_line_id": sale_line["id"],
                    "quantity": 2,
                    "return_to_stock": True,
                }
            ],
        },
    )
    assert second.status_code == 422
    assert second.json()["message"] == "Refund quantity exceeds remaining sold quantity"

    refunded_total = db_session.scalar(
        select(RefundItem.quantity).where(
            RefundItem.sale_line_id == sale_line["id"],
        )
    )
    assert refunded_total == 2


def test_refund_without_stock_return_keeps_batch_qty(client, owner_headers, db_session: Session):
    medicine = _create_medicine(client, owner_headers)
    batch = _create_batch(client, owner_headers, medicine["id"], quantity_received=10, selling_price=9.0)
    sale = _create_sale(client, owner_headers, medicine["id"], quantity=2)
    sale_line = sale["lines"][0]

    before = db_session.get(Batch, batch["id"])
    assert before is not None
    assert before.quantity_on_hand == 8

    response = client.post(
        "/api/refunds",
        headers=owner_headers,
        json={
            "sale_id": sale["id"],
            "reason": "Damaged return not for stock",
            "refund_method": "momo",
            "lines": [
                {
                    "sale_line_id": sale_line["id"],
                    "quantity": 1,
                    "return_to_stock": False,
                }
            ],
        },
    )
    assert response.status_code == 201, response.json()
    assert Decimal(str(response.json()["data"]["total_amount"])) == Decimal("9.00")

    after = db_session.get(Batch, batch["id"])
    assert after is not None
    assert after.quantity_on_hand == 8

    refund_id = response.json()["data"]["id"]
    movement = db_session.scalar(
        select(InventoryMovement).where(
            InventoryMovement.reference_type == "refund",
            InventoryMovement.reference_id == refund_id,
        )
    )
    assert movement is None


def test_refund_unknown_sale_returns_404(client, owner_headers):
    response = client.post(
        "/api/refunds",
        headers=owner_headers,
        json={
            "sale_id": 999999,
            "reason": "Unknown sale",
            "refund_method": "cash",
            "lines": [{"sale_line_id": 1, "quantity": 1, "return_to_stock": True}],
        },
    )
    assert response.status_code == 404
    assert response.json()["message"] == "Sale not found"


def test_refund_line_from_other_sale_returns_422(client, owner_headers):
    medicine_a = _create_medicine(client, owner_headers)
    _create_batch(client, owner_headers, medicine_a["id"], quantity_received=10, selling_price=18.0)
    sale_a = _create_sale(client, owner_headers, medicine_a["id"], quantity=1)

    medicine_b = _create_medicine(client, owner_headers)
    _create_batch(client, owner_headers, medicine_b["id"], quantity_received=10, selling_price=18.0)
    sale_b = _create_sale(client, owner_headers, medicine_b["id"], quantity=1)

    foreign_line_id = sale_b["lines"][0]["id"]
    response = client.post(
        "/api/refunds",
        headers=owner_headers,
        json={
            "sale_id": sale_a["id"],
            "reason": "Wrong line reference",
            "refund_method": "cash",
            "lines": [{"sale_line_id": foreign_line_id, "quantity": 1, "return_to_stock": True}],
        },
    )
    assert response.status_code == 422
    assert response.json()["message"] == "One or more sale lines do not belong to the sale"


def test_staff_cannot_create_refund(client, staff_headers):
    response = client.post(
        "/api/refunds",
        headers=staff_headers,
        json={
            "sale_id": 1,
            "reason": "No permission",
            "refund_method": "cash",
            "lines": [{"sale_line_id": 1, "quantity": 1, "return_to_stock": True}],
        },
    )
    assert response.status_code == 403
    assert response.json()["message"] == "Insufficient permissions"


def test_refund_requires_auth(client):
    response = client.post(
        "/api/refunds",
        json={
            "sale_id": 1,
            "reason": "No auth",
            "refund_method": "cash",
            "lines": [{"sale_line_id": 1, "quantity": 1, "return_to_stock": True}],
        },
    )
    assert response.status_code == 401
    assert response.json()["message"] == "Authentication required"
