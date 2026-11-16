from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import SessionLocal, engine, get_db
from app.core.security import hash_password
from app.main import app
from app.models.audit_log import AuditLog
from app.models.batch import Batch
from app.models.inventory_movement import InventoryMovement
from app.models.medicine import Medicine
from app.models.role import Role
from app.models.user import User
from app.modules.inventory import repository, service


@pytest.fixture
def adjustment_db(client):
    """API commits release savepoints; the test's outer transaction rolls back."""
    with engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        previous = app.dependency_overrides.get(get_db)
        app.dependency_overrides[get_db] = lambda: session
        try:
            yield session
        finally:
            if previous is None:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = previous
            session.close()
            transaction.rollback()


def _login(client, email, password):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


@pytest.fixture
def owner_headers(client, adjustment_db):
    return _login(client, settings.demo_email, settings.demo_password)


@pytest.fixture
def role_headers(client, adjustment_db):
    def create(role_name):
        suffix = uuid4().hex
        role = adjustment_db.scalar(select(Role).where(Role.name == role_name))
        user = User(full_name=f"Adjustment {role_name}", email=f"{suffix}@adjustments.local",
                    username=suffix, password_hash=hash_password("AdjustmentPass123!"),
                    role_id=role.id, status="active")
        adjustment_db.add(user)
        adjustment_db.commit()
        return _login(client, user.email, "AdjustmentPass123!"), user.id
    return create


@pytest.fixture
def batch(client, owner_headers):
    response = client.post("/api/medicines", headers=owner_headers,
                           json={"name": f"Adjustment medicine {uuid4().hex}"})
    assert response.status_code == 201
    response = client.post("/api/batches", headers=owner_headers, json={
        "medicine_id": response.json()["data"]["id"], "batch_number": uuid4().hex,
        "expiry_date": (date.today() + timedelta(days=180)).isoformat(),
        "cost_price": "2.50", "selling_price": "4.00", "quantity_received": 10,
    })
    assert response.status_code == 201
    return response.json()["data"]


def _adjust(client, batch_id, headers=None, **overrides):
    payload = {"quantity_change": -2, "reason": "Shelf count correction"}
    payload.update(overrides)
    return client.post(f"/api/batches/{batch_id}/adjustments", headers=headers, json=payload)


def _state(db, batch_id):
    db.expire_all()
    batch = db.get(Batch, batch_id)
    movements = db.scalar(select(func.count()).select_from(InventoryMovement).where(
        InventoryMovement.batch_id == batch_id))
    audits = db.scalar(select(func.count()).select_from(AuditLog).where(
        AuditLog.entity_type == "batch", AuditLog.entity_id == batch_id))
    return batch.quantity_on_hand, batch.quantity_received, batch.status, movements, audits


def test_pharmacist_adjustment_writes_one_movement_and_audit(client, adjustment_db, batch, role_headers):
    headers, actor_id = role_headers("pharmacist")
    before = _state(adjustment_db, batch["id"])
    response = _adjust(client, batch["id"], headers, reason="  Damaged blister packs  ")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["errors"] == []
    assert body["data"] == dict(batch, quantity_on_hand=8)
    assert _state(adjustment_db, batch["id"]) == (8, 10, batch["status"], before[3] + 1, before[4] + 1)
    movements = list(adjustment_db.scalars(select(InventoryMovement).where(
        InventoryMovement.batch_id == batch["id"], InventoryMovement.movement_type == "adjustment")))
    assert len(movements) == 1
    movement = movements[0]
    assert (movement.medicine_id, movement.quantity_change, movement.reference_type,
            movement.reference_id, movement.user_id, movement.reason) == (
        batch["medicine_id"], -2, "adjustment", None, actor_id, "Damaged blister packs")
    audits = list(adjustment_db.scalars(select(AuditLog).where(
        AuditLog.entity_type == "batch", AuditLog.entity_id == batch["id"],
        AuditLog.action == "batch.adjusted")))
    assert len(audits) == 1
    assert audits[0].user_id == actor_id
    assert audits[0].details == {"batch_id": batch["id"], "quantity_change": -2,
                                "reason": "Damaged blister packs", "quantity_on_hand": 8}


@pytest.mark.parametrize("role", ["owner", "admin"])
def test_positive_adjustment_allowed_for_owner_and_admin(client, adjustment_db, batch, role_headers, role):
    headers, _ = role_headers(role)
    response = _adjust(client, batch["id"], headers, quantity_change=4)
    assert response.status_code == 200
    assert response.json()["data"] == dict(batch, quantity_on_hand=14)
    assert _state(adjustment_db, batch["id"])[0] == 14


@pytest.mark.parametrize("batch_status", ["active", "expired"])
def test_adjustment_to_zero_preserves_status(client, adjustment_db, batch, owner_headers, batch_status):
    adjustment_db.get(Batch, batch["id"]).status = batch_status
    adjustment_db.commit()
    response = _adjust(client, batch["id"], owner_headers, quantity_change=-10)
    assert response.status_code == 200
    assert response.json()["data"]["quantity_on_hand"] == 0
    assert response.json()["data"]["status"] == batch_status
    assert _state(adjustment_db, batch["id"])[:3] == (0, 10, batch_status)


def test_negative_result_leaves_no_writes(client, adjustment_db, batch, owner_headers):
    before = _state(adjustment_db, batch["id"])
    response = _adjust(client, batch["id"], owner_headers, quantity_change=-11)
    assert response.status_code == 422
    assert response.json()["message"] == "Adjustment would make quantity negative"
    assert response.json()["success"] is False
    assert _state(adjustment_db, batch["id"]) == before


@pytest.mark.parametrize("payload", [
    {"quantity_change": 0, "reason": "Count"}, {"quantity_change": -1},
    {"quantity_change": -1, "reason": ""}, {"quantity_change": -1, "reason": " \t\n "},
    {"quantity_change": -1, "reason": " ab "}, {"quantity_change": -1, "reason": None},
    {"quantity_change": 1.5, "reason": "Count"}, {"quantity_change": 2.0, "reason": "Count"},
    {"quantity_change": "2", "reason": "Count"}, {"quantity_change": True, "reason": "Count"},
    {"reason": "Count"},
])
def test_invalid_payload_leaves_no_writes(client, adjustment_db, batch, owner_headers, payload):
    before = _state(adjustment_db, batch["id"])
    response = client.post(f"/api/batches/{batch['id']}/adjustments", headers=owner_headers, json=payload)
    assert response.status_code == 422
    assert response.json()["success"] is False
    assert _state(adjustment_db, batch["id"]) == before


def test_unknown_batch_returns_404(client, adjustment_db, owner_headers):
    before = tuple(adjustment_db.scalar(select(func.count()).select_from(model))
                   for model in (InventoryMovement, AuditLog))
    response = _adjust(client, 2147483647, owner_headers)
    assert response.status_code == 404
    assert response.json()["message"] == "Batch not found"
    assert tuple(adjustment_db.scalar(select(func.count()).select_from(model))
                 for model in (InventoryMovement, AuditLog)) == before


def test_void_batch_leaves_no_writes(client, adjustment_db, batch, owner_headers):
    adjustment_db.get(Batch, batch["id"]).status = "void"
    adjustment_db.commit()
    before = _state(adjustment_db, batch["id"])
    assert _adjust(client, batch["id"], owner_headers).status_code == 409
    assert _state(adjustment_db, batch["id"]) == before


def test_staff_forbidden(client, adjustment_db, batch, role_headers):
    headers, _ = role_headers("staff")
    before = _state(adjustment_db, batch["id"])
    assert _adjust(client, batch["id"], headers).status_code == 403
    assert _state(adjustment_db, batch["id"]) == before


def test_unauthenticated_forbidden(client, adjustment_db, batch):
    before = _state(adjustment_db, batch["id"])
    assert _adjust(client, batch["id"]).status_code == 401
    assert _state(adjustment_db, batch["id"]) == before


@pytest.mark.parametrize("failure_point", ["audit", "commit"])
def test_internal_failure_rolls_back_all_writes(client, adjustment_db, batch, owner_headers, monkeypatch, failure_point):
    before = _state(adjustment_db, batch["id"])
    if failure_point == "audit":
        original = service.create_audit_log

        def fail(*args, **kwargs):
            original(*args, **kwargs)
            raise RuntimeError("Injected failure after audit insert")
        monkeypatch.setattr(service, "create_audit_log", fail)
    else:
        def fail():
            raise RuntimeError("Injected failure before commit")
        monkeypatch.setattr(adjustment_db, "commit", fail)
    with pytest.raises(RuntimeError, match="Injected failure"):
        _adjust(client, batch["id"], owner_headers)
    assert _state(adjustment_db, batch["id"]) == before


def test_concurrent_adjustments_cannot_oversell(client, monkeypatch):
    """Independent connections require PostgreSQL to serialize the row locks."""
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    headers = _login(client, settings.demo_email, settings.demo_password)
    with SessionLocal() as db:
        medicine = Medicine(name=f"Concurrent adjustment {uuid4().hex}")
        db.add(medicine)
        db.flush()
        batch = Batch(medicine_id=medicine.id, batch_number=uuid4().hex,
                      cost_price=Decimal("2.50"), selling_price=Decimal("4.00"),
                      quantity_on_hand=10, quantity_received=10, status="active")
        db.add(batch)
        db.commit()
        batch_id, medicine_id = batch.id, medicine.id

    barrier = Barrier(2)
    original = repository.get_batch_for_update

    def lock(db, requested_id):
        barrier.wait(timeout=10)
        return original(db, requested_id)

    monkeypatch.setattr(repository, "get_batch_for_update", lock)

    def request():
        with TestClient(app) as concurrent_client:
            return _adjust(concurrent_client, batch_id, headers, quantity_change=-7)

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda _: request(), range(2)))
        assert sorted(response.status_code for response in responses) == [200, 422]
        with SessionLocal() as db:
            assert _state(db, batch_id) == (3, 10, "active", 1, 1)
    finally:
        with SessionLocal() as db:
            db.execute(delete(AuditLog).where(AuditLog.entity_type == "batch", AuditLog.entity_id == batch_id))
            db.execute(delete(InventoryMovement).where(InventoryMovement.batch_id == batch_id))
            db.execute(delete(Batch).where(Batch.id == batch_id))
            db.execute(delete(Medicine).where(Medicine.id == medicine_id))
            db.commit()
