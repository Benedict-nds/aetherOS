from datetime import date, timedelta
from uuid import uuid4

from sqlalchemy import func, select
import pytest

from app.core.config import settings
from app.core.security import hash_password
from app.models.batch import Batch
from app.models.inventory_movement import InventoryMovement
from app.models.role import Role
from app.models.supplier import Supplier
from app.models.user import User
from app.modules.inventory.service import MOVEMENT_TYPE_STOCK_IN


def _medicine(client, headers):
    suffix = uuid4().hex[:8]
    response = client.post("/api/medicines", headers=headers, json={"name": f"Receipt Med {suffix}"})
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _supplier(client, headers):
    response = client.post("/api/suppliers", headers=headers, json={"name": f"Receipt Supplier {uuid4().hex}"})
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _ensure_role_user(db, role_name):
    email = f"receipt.{role_name}@aetherqore.local"
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        role = db.scalar(select(Role).where(Role.name == role_name))
        user = User(full_name=f"Receipt {role_name}", email=email, username=f"receipt{role_name}", password_hash=hash_password("ReceiptPass123!"), role_id=role.id, status="active")
        db.add(user)
        db.commit()
    response_user = user
    return response_user


def _headers(client, email, password):
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['data']['access_token']}"}


@pytest.fixture
def owner_headers(client):
    return _headers(client, settings.demo_email, settings.demo_password)


@pytest.fixture
def pharmacist_headers(client, db_session):
    user = _ensure_role_user(db_session, "pharmacist")
    return _headers(client, user.email, "ReceiptPass123!")


@pytest.fixture
def staff_headers(client, db_session):
    user = _ensure_role_user(db_session, "staff")
    return _headers(client, user.email, "ReceiptPass123!")


def _line(medicine_id, **overrides):
    data = {"medicine_id": medicine_id, "batch_number": f"R-{uuid4().hex[:10]}", "expiry_date": (date.today() + timedelta(days=20)).isoformat(), "cost_price": "2.50", "selling_price": "4.00", "quantity_received": 7}
    data.update(overrides)
    return data


def test_receipt_creates_supplier_batches_and_stock_in_movements(client, owner_headers, db_session):
    supplier_id = _supplier(client, owner_headers)
    med_a, med_b = _medicine(client, owner_headers), _medicine(client, owner_headers)
    response = client.post("/api/purchases/receipts", headers=owner_headers, json={"supplier_id": supplier_id, "lines": [_line(med_a), _line(med_b)]})
    assert response.status_code == 201, response.json()
    batches = response.json()["data"]["lines"]
    assert len(batches) == 2
    for batch in batches:
        assert batch["supplier_id"] == supplier_id
        assert batch["quantity_on_hand"] == 7
        movement = db_session.scalar(select(InventoryMovement).where(InventoryMovement.batch_id == batch["id"]))
        assert movement.movement_type == MOVEMENT_TYPE_STOCK_IN
        assert movement.quantity_change == 7


def test_receipt_past_expiry_sets_expired(client, owner_headers):
    response = client.post("/api/purchases/receipts", headers=owner_headers, json={"supplier_id": _supplier(client, owner_headers), "lines": [_line(_medicine(client, owner_headers), expiry_date=(date.today() - timedelta(days=1)).isoformat())]})
    assert response.status_code == 201
    assert response.json()["data"]["lines"][0]["status"] == "expired"


def test_receipt_missing_and_inactive_supplier(client, owner_headers, db_session):
    payload = {"supplier_id": 999999, "lines": [_line(_medicine(client, owner_headers))]}
    assert client.post("/api/purchases/receipts", headers=owner_headers, json=payload).status_code == 404
    inactive = Supplier(name=f"Inactive receipt supplier {uuid4().hex}", is_active=False)
    db_session.add(inactive)
    db_session.commit()
    payload["supplier_id"] = inactive.id
    assert client.post("/api/purchases/receipts", headers=owner_headers, json=payload).status_code == 409


def test_receipt_duplicate_batch_conflicts(client, owner_headers):
    supplier_id = _supplier(client, owner_headers)
    med_id = _medicine(client, owner_headers)
    line = _line(med_id)
    payload = {"supplier_id": supplier_id, "lines": [line]}
    assert client.post("/api/purchases/receipts", headers=owner_headers, json=payload).status_code == 201
    assert client.post("/api/purchases/receipts", headers=owner_headers, json=payload).status_code == 409


def test_receipt_is_atomic_when_later_line_fails(client, owner_headers, db_session):
    supplier_id = _supplier(client, owner_headers)
    med_id = _medicine(client, owner_headers)
    duplicate = _line(med_id)
    assert client.post("/api/purchases/receipts", headers=owner_headers, json={"supplier_id": supplier_id, "lines": [duplicate]}).status_code == 201
    before_batches = db_session.scalar(select(func.count()).select_from(Batch))
    before_movements = db_session.scalar(select(func.count()).select_from(InventoryMovement))
    payload = {"supplier_id": supplier_id, "lines": [_line(_medicine(client, owner_headers)), duplicate]}
    response = client.post("/api/purchases/receipts", headers=owner_headers, json=payload)
    assert response.status_code == 409
    assert db_session.scalar(select(func.count()).select_from(Batch)) == before_batches
    assert db_session.scalar(select(func.count()).select_from(InventoryMovement)) == before_movements


def test_receipt_auth_and_roles(client, owner_headers, staff_headers, pharmacist_headers):
    supplier_id = _supplier(client, owner_headers)
    payload = {"supplier_id": supplier_id, "lines": [_line(_medicine(client, owner_headers))]}
    assert client.post("/api/purchases/receipts", json=payload).status_code == 401
    assert client.post("/api/purchases/receipts", headers=staff_headers, json=payload).status_code == 403
    assert client.post("/api/purchases/receipts", headers=pharmacist_headers, json=payload).status_code == 201


def test_receipt_invalid_line_validation(client, owner_headers):
    response = client.post("/api/purchases/receipts", headers=owner_headers, json={"supplier_id": 1, "lines": []})
    assert response.status_code == 422
