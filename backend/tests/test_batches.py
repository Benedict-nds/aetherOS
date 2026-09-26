from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.batch import Batch
from app.models.inventory_movement import InventoryMovement
from app.models.role import Role
from app.models.user import User
from app.modules.audit.service import ACTION_CREATE, ENTITY_TYPE_BATCH
from app.modules.inventory import service as inventory_service
from app.modules.inventory.service import MOVEMENT_TYPE_STOCK_IN, REFERENCE_TYPE_BATCH

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
        full_name=f"Batch {role_name.title()}",
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
    _ensure_user(db_session, "staff", "batch.staff@aetherqore.local", "batchstaff")
    return _login(client, "batch.staff@aetherqore.local", FIXTURE_PASSWORD)


@pytest.fixture
def pharmacist_headers(client, db_session: Session):
    _ensure_user(
        db_session,
        "pharmacist",
        "batch.pharmacist@aetherqore.local",
        "batchpharmacist",
    )
    return _login(client, "batch.pharmacist@aetherqore.local", FIXTURE_PASSWORD)


def _create_medicine(client, headers, name: str | None = None) -> dict:
    suffix = uuid4().hex[:8]
    response = client.post(
        "/api/medicines",
        headers=headers,
        json={
            "name": name or f"Amoxicillin {suffix}",
            "generic_name": "Amoxicillin",
            "dosage_form": "Capsule",
            "strength": "500mg",
            "barcode": f"BATCH{suffix.upper()}",
        },
    )
    assert response.status_code == 201, response.json()
    return response.json()["data"]


def _batch_payload(medicine_id: int, **overrides) -> dict:
    payload = {
        "medicine_id": medicine_id,
        "batch_number": f"AMX-{uuid4().hex[:6].upper()}",
        "expiry_date": (date.today() + timedelta(days=365)).isoformat(),
        "cost_price": 12.5,
        "selling_price": 18.0,
        "quantity_received": 100,
    }
    payload.update(overrides)
    return payload


def test_create_medicine_and_get_detail(client, owner_headers):
    created = _create_medicine(client, owner_headers, name="Metformin 850mg")

    response = client.get(f"/api/medicines/{created['id']}", headers=owner_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["id"] == created["id"]
    assert data["name"] == "Metformin 850mg"
    assert data["quantity_on_hand"] == 0
    assert "password_hash" not in data


def test_get_medicine_not_found(client, owner_headers):
    response = client.get("/api/medicines/999999", headers=owner_headers)
    assert response.status_code == 404
    assert response.json()["message"] == "Medicine not found"


def test_create_batch_creates_stock_in_movement(
    client,
    owner_headers,
    db_session: Session,
):
    medicine = _create_medicine(client, owner_headers)
    payload = _batch_payload(medicine["id"], batch_number="AMX-2231")

    response = client.post("/api/batches", headers=owner_headers, json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True

    batch = body["data"]
    assert batch["medicine_id"] == medicine["id"]
    assert batch["batch_number"] == "AMX-2231"
    assert batch["quantity_on_hand"] == 100
    assert batch["status"] == "active"
    assert batch["supplier_id"] is None
    assert Decimal(str(batch["cost_price"])) == Decimal("12.50")
    assert Decimal(str(batch["selling_price"])) == Decimal("18.00")

    owner = db_session.scalar(select(User).where(User.email == settings.demo_email))
    movement = db_session.scalar(
        select(InventoryMovement)
        .where(InventoryMovement.batch_id == batch["id"])
        .order_by(InventoryMovement.id.desc())
    )
    assert movement is not None
    assert movement.medicine_id == medicine["id"]
    assert movement.movement_type == MOVEMENT_TYPE_STOCK_IN
    assert movement.quantity_change == 100
    assert movement.reference_type == REFERENCE_TYPE_BATCH
    assert movement.user_id == owner.id

    audit = db_session.scalar(
        select(AuditLog)
        .where(
            AuditLog.action == ACTION_CREATE,
            AuditLog.entity_type == ENTITY_TYPE_BATCH,
            AuditLog.entity_id == batch["id"],
        )
        .order_by(AuditLog.id.desc())
    )
    assert audit is not None
    assert audit.user_id == owner.id


def test_batch_creation_rolls_back_when_movement_fails(
    client,
    owner_headers,
    db_session: Session,
    monkeypatch,
):
    medicine = _create_medicine(client, owner_headers)
    payload = _batch_payload(medicine["id"], batch_number="ROLLBACK-1")

    def fail_insert(*args, **kwargs):
        raise RuntimeError("forced movement failure")

    monkeypatch.setattr(
        inventory_service,
        "insert_inventory_movement",
        fail_insert,
    )

    before_batches = db_session.scalar(select(func.count()).select_from(Batch)) or 0
    before_movements = (
        db_session.scalar(select(func.count()).select_from(InventoryMovement)) or 0
    )

    with pytest.raises(RuntimeError, match="forced movement failure"):
        client.post("/api/batches", headers=owner_headers, json=payload)

    db_session.expire_all()
    after_batches = db_session.scalar(select(func.count()).select_from(Batch)) or 0
    after_movements = (
        db_session.scalar(select(func.count()).select_from(InventoryMovement)) or 0
    )
    leftover = db_session.scalar(
        select(Batch).where(
            Batch.medicine_id == medicine["id"],
            Batch.batch_number == "ROLLBACK-1",
        )
    )

    assert leftover is None
    assert after_batches == before_batches
    assert after_movements == before_movements


def test_duplicate_batch_number_same_medicine_returns_409(client, owner_headers):
    medicine = _create_medicine(client, owner_headers)
    payload = _batch_payload(medicine["id"], batch_number="DUP-001")

    first = client.post("/api/batches", headers=owner_headers, json=payload)
    assert first.status_code == 201

    second = client.post("/api/batches", headers=owner_headers, json=payload)
    assert second.status_code == 409
    assert second.json()["success"] is False
    assert "already exists" in second.json()["message"].lower()


def test_same_batch_number_allowed_on_different_medicines(client, owner_headers):
    first_medicine = _create_medicine(client, owner_headers)
    second_medicine = _create_medicine(client, owner_headers)

    first = client.post(
        "/api/batches",
        headers=owner_headers,
        json=_batch_payload(first_medicine["id"], batch_number="SHARED-1"),
    )
    second = client.post(
        "/api/batches",
        headers=owner_headers,
        json=_batch_payload(second_medicine["id"], batch_number="SHARED-1"),
    )

    assert first.status_code == 201
    assert second.status_code == 201


def test_staff_cannot_create_batch(client, owner_headers, staff_headers):
    medicine = _create_medicine(client, owner_headers)
    response = client.post(
        "/api/batches",
        headers=staff_headers,
        json=_batch_payload(medicine["id"]),
    )
    assert response.status_code == 403
    assert response.json()["message"] == "Insufficient permissions"


def test_pharmacist_can_create_batch(client, pharmacist_headers):
    medicine = _create_medicine(client, pharmacist_headers)
    response = client.post(
        "/api/batches",
        headers=pharmacist_headers,
        json=_batch_payload(medicine["id"]),
    )
    assert response.status_code == 201


def test_unauthenticated_create_batch_returns_401(client):
    response = client.post(
        "/api/batches",
        json=_batch_payload(1),
    )
    assert response.status_code == 401
    assert response.json()["success"] is False


def test_staff_can_list_batches_and_movements(
    client,
    owner_headers,
    staff_headers,
):
    medicine = _create_medicine(client, owner_headers)
    created = client.post(
        "/api/batches",
        headers=owner_headers,
        json=_batch_payload(medicine["id"]),
    )
    assert created.status_code == 201

    batches = client.get(
        f"/api/medicines/{medicine['id']}/batches",
        headers=staff_headers,
    )
    movements = client.get("/api/inventory/movements", headers=staff_headers)

    assert batches.status_code == 200
    assert movements.status_code == 200


def test_missing_medicine_returns_404_on_create_and_list(client, owner_headers):
    create_response = client.post(
        "/api/batches",
        headers=owner_headers,
        json=_batch_payload(999999),
    )
    list_response = client.get(
        "/api/medicines/999999/batches",
        headers=owner_headers,
    )

    assert create_response.status_code == 404
    assert list_response.status_code == 404


def test_zero_quantity_rejected(client, owner_headers):
    medicine = _create_medicine(client, owner_headers)
    response = client.post(
        "/api/batches",
        headers=owner_headers,
        json=_batch_payload(medicine["id"], quantity_received=0),
    )
    assert response.status_code == 422
    assert response.json()["success"] is False


def test_negative_quantity_rejected(client, owner_headers):
    medicine = _create_medicine(client, owner_headers)
    response = client.post(
        "/api/batches",
        headers=owner_headers,
        json=_batch_payload(medicine["id"], quantity_received=-5),
    )
    assert response.status_code == 422


def test_list_movements_returns_stock_in_row(client, owner_headers):
    medicine = _create_medicine(client, owner_headers)
    created = client.post(
        "/api/batches",
        headers=owner_headers,
        json=_batch_payload(medicine["id"], quantity_received=40),
    )
    batch_id = created.json()["data"]["id"]

    response = client.get("/api/inventory/movements", headers=owner_headers)
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["total"] >= 1
    match = next(item for item in body["items"] if item["batch_id"] == batch_id)
    assert match["movement_type"] == "stock_in"
    assert match["quantity_change"] == 40
    assert match["reference_type"] == "batch"
    assert match["medicine_id"] == medicine["id"]


def test_movement_filters(client, owner_headers):
    first_medicine = _create_medicine(client, owner_headers)
    second_medicine = _create_medicine(client, owner_headers)

    first_batch = client.post(
        "/api/batches",
        headers=owner_headers,
        json=_batch_payload(first_medicine["id"], quantity_received=10),
    ).json()["data"]
    second_batch = client.post(
        "/api/batches",
        headers=owner_headers,
        json=_batch_payload(second_medicine["id"], quantity_received=20),
    ).json()["data"]

    by_medicine = client.get(
        "/api/inventory/movements",
        headers=owner_headers,
        params={"medicine_id": first_medicine["id"]},
    )
    by_batch = client.get(
        "/api/inventory/movements",
        headers=owner_headers,
        params={"batch_id": second_batch["id"]},
    )
    by_both = client.get(
        "/api/inventory/movements",
        headers=owner_headers,
        params={
            "medicine_id": first_medicine["id"],
            "batch_id": first_batch["id"],
        },
    )

    assert by_medicine.status_code == 200
    assert by_batch.status_code == 200
    assert by_both.status_code == 200

    medicine_items = by_medicine.json()["data"]["items"]
    batch_items = by_batch.json()["data"]["items"]
    both_items = by_both.json()["data"]["items"]

    assert medicine_items
    assert all(item["medicine_id"] == first_medicine["id"] for item in medicine_items)
    assert batch_items
    assert all(item["batch_id"] == second_batch["id"] for item in batch_items)
    assert both_items
    assert all(
        item["medicine_id"] == first_medicine["id"]
        and item["batch_id"] == first_batch["id"]
        for item in both_items
    )


def test_list_batches_for_medicine(client, owner_headers):
    medicine = _create_medicine(client, owner_headers)
    other = _create_medicine(client, owner_headers)

    first = client.post(
        "/api/batches",
        headers=owner_headers,
        json=_batch_payload(medicine["id"], batch_number="LIST-A"),
    ).json()["data"]
    second = client.post(
        "/api/batches",
        headers=owner_headers,
        json=_batch_payload(medicine["id"], batch_number="LIST-B"),
    ).json()["data"]
    client.post(
        "/api/batches",
        headers=owner_headers,
        json=_batch_payload(other["id"], batch_number="LIST-OTHER"),
    )

    response = client.get(
        f"/api/medicines/{medicine['id']}/batches",
        headers=owner_headers,
    )
    assert response.status_code == 200
    batches = response.json()["data"]
    batch_ids = {item["id"] for item in batches}
    assert first["id"] in batch_ids
    assert second["id"] in batch_ids
    assert all(item["medicine_id"] == medicine["id"] for item in batches)


def test_expired_batch_can_be_created(client, owner_headers):
    medicine = _create_medicine(client, owner_headers)
    response = client.post(
        "/api/batches",
        headers=owner_headers,
        json=_batch_payload(
            medicine["id"],
            expiry_date=(date.today() - timedelta(days=1)).isoformat(),
        ),
    )
    assert response.status_code == 201
    assert response.json()["data"]["status"] == "expired"
    assert response.json()["data"]["quantity_on_hand"] == 100


def test_derived_medicine_quantity_excludes_void_batches(
    client,
    owner_headers,
    db_session: Session,
):
    medicine = _create_medicine(client, owner_headers)
    client.post(
        "/api/batches",
        headers=owner_headers,
        json=_batch_payload(medicine["id"], quantity_received=40),
    )
    client.post(
        "/api/batches",
        headers=owner_headers,
        json=_batch_payload(medicine["id"], quantity_received=60),
    )

    void_batch = Batch(
        medicine_id=medicine["id"],
        batch_number="VOID-1",
        expiry_date=date.today() + timedelta(days=30),
        cost_price=Decimal("1.00"),
        selling_price=Decimal("2.00"),
        quantity_on_hand=999,
        quantity_received=999,
        status="void",
        supplier_id=None,
    )
    db_session.add(void_batch)
    db_session.commit()

    response = client.get(f"/api/medicines/{medicine['id']}", headers=owner_headers)
    assert response.status_code == 200
    assert response.json()["data"]["quantity_on_hand"] == 100
