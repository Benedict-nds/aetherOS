from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.batch import Batch
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


def _get_or_create_user(
    db_session: Session,
    *,
    full_name: str,
    email: str,
    username: str,
    password: str,
    role_name: str,
) -> User:
    user = db_session.scalar(select(User).where(User.email == email))
    if user is not None:
        return user

    role = db_session.scalar(select(Role).where(Role.name == role_name))
    assert role is not None
    user = User(
        full_name=full_name,
        email=email,
        username=username,
        password_hash=hash_password(password),
        role_id=role.id,
        status="active",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def staff_headers(client, db_session: Session):
    _get_or_create_user(
        db_session,
        full_name="Staff User",
        email="staff.medicines@aetherqore.local",
        username="staffmeduser",
        password="StaffPass123!",
        role_name="staff",
    )
    return _login(client, "staff.medicines@aetherqore.local", "StaffPass123!")


@pytest.fixture
def pharmacist_headers(client, db_session: Session):
    _get_or_create_user(
        db_session,
        full_name="Pharmacist User",
        email="pharmacist.medicines@aetherqore.local",
        username="pharmacistmeduser",
        password="PharmaPass123!",
        role_name="pharmacist",
    )
    return _login(client, "pharmacist.medicines@aetherqore.local", "PharmaPass123!")


@pytest.fixture
def admin_headers(client, db_session: Session):
    _get_or_create_user(
        db_session,
        full_name="Admin User",
        email="admin.medicines@aetherqore.local",
        username="adminmeduser",
        password="AdminPass123!",
        role_name="admin",
    )
    return _login(client, "admin.medicines@aetherqore.local", "AdminPass123!")


def test_unauthenticated_medicines_returns_401(client):
    response = client.get("/api/medicines")
    assert response.status_code == 401


def test_staff_cannot_create_medicine(client, staff_headers):
    response = client.post(
        "/api/medicines",
        headers=staff_headers,
        json={
            "name": "Test Medicine",
            "barcode": "STAFFTEST001",
            "reorder_level": 0,
        },
    )
    assert response.status_code == 403
    assert response.json()["message"] == "Insufficient permissions"


@pytest.mark.parametrize("headers_fixture", ["pharmacist_headers", "admin_headers", "owner_headers"])
def test_authorized_roles_can_create_medicine(client, headers_fixture, request):
    headers = request.getfixturevalue(headers_fixture)
    barcode = f"CREATE{headers_fixture.upper()}001"
    response = client.post(
        "/api/medicines",
        headers=headers,
        json={
            "name": f"Created by {headers_fixture}",
            "barcode": barcode,
            "reorder_level": 5,
        },
    )
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == f"Created by {headers_fixture}"
    assert data["barcode"] == barcode
    assert data["is_active"] is True


def test_search_medicines_by_barcode_and_name(client, owner_headers):
    by_barcode = client.get(
        "/api/medicines",
        headers=owner_headers,
        params={"q": "AMOX500001"},
    )
    assert by_barcode.status_code == 200
    results = by_barcode.json()["data"]
    assert len(results) == 1
    assert results[0]["barcode"] == "AMOX500001"

    by_name = client.get(
        "/api/medicines",
        headers=owner_headers,
        params={"q": "Metformin"},
    )
    assert by_name.status_code == 200
    results = by_name.json()["data"]
    assert any(item["generic_name"] == "Metformin" for item in results)


def test_duplicate_barcode_rejected(client, owner_headers):
    response = client.post(
        "/api/medicines",
        headers=owner_headers,
        json={
            "name": "Duplicate Barcode Medicine",
            "barcode": "AMOX500001",
            "reorder_level": 0,
        },
    )
    assert response.status_code == 409
    assert response.json()["message"] == "Barcode already exists"


def test_patch_deactivates_and_list_hides_by_default(client, pharmacist_headers):
    create_response = client.post(
        "/api/medicines",
        headers=pharmacist_headers,
        json={
            "name": "Temporary Medicine",
            "barcode": "TEMP999001",
            "reorder_level": 0,
        },
    )
    assert create_response.status_code == 201
    medicine_id = create_response.json()["data"]["id"]

    patch_response = client.patch(
        f"/api/medicines/{medicine_id}",
        headers=pharmacist_headers,
        json={"is_active": False},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["data"]["is_active"] is False

    list_response = client.get("/api/medicines", headers=pharmacist_headers)
    assert list_response.status_code == 200
    ids = [item["id"] for item in list_response.json()["data"]]
    assert medicine_id not in ids

    inactive_response = client.get(
        "/api/medicines",
        headers=pharmacist_headers,
        params={"is_active": False},
    )
    assert inactive_response.status_code == 200
    inactive_ids = [item["id"] for item in inactive_response.json()["data"]]
    assert medicine_id in inactive_ids


def _medicine_from_list(client, headers, *, barcode: str) -> dict:
    response = client.get("/api/medicines", headers=headers, params={"q": barcode})
    assert response.status_code == 200
    rows = response.json()["data"]
    assert len(rows) == 1
    return rows[0]


def _create_batch(client, headers, medicine_id: int, **overrides) -> dict:
    payload = {
        "medicine_id": medicine_id,
        "batch_number": f"LIST-{uuid4().hex[:6].upper()}",
        "expiry_date": (date.today() + timedelta(days=180)).isoformat(),
        "cost_price": 5.0,
        "selling_price": 10.0,
        "quantity_received": 10,
    }
    payload.update(overrides)
    response = client.post("/api/batches", headers=headers, json=payload)
    assert response.status_code == 201, response.json()
    return response.json()["data"]


def test_list_seeded_medicine_without_batches_shows_critical_stock(client, owner_headers):
    row = _medicine_from_list(client, owner_headers, barcode="MET500001")
    detail = client.get(f"/api/medicines/{row['id']}", headers=owner_headers)
    assert detail.status_code == 200
    data = detail.json()["data"]

    for payload in (row, data):
        assert payload["quantity_on_hand"] == 0
        assert payload["stock_status"] == "critical"
        assert payload["nearest_batch_number"] is None
        assert payload["nearest_expiry_date"] is None


def test_list_shows_low_stock_after_batch_received(client, owner_headers):
    row = _medicine_from_list(client, owner_headers, barcode="MET500001")
    batch = _create_batch(
        client,
        owner_headers,
        row["id"],
        batch_number="MET-1181",
        quantity_received=5,
    )

    list_row = _medicine_from_list(client, owner_headers, barcode="MET500001")
    assert list_row["quantity_on_hand"] == 5
    assert list_row["stock_status"] == "low"
    assert list_row["nearest_batch_number"] == batch["batch_number"]
    assert list_row["nearest_expiry_date"] == batch["expiry_date"]


def test_list_quantity_sums_batches_and_nearest_is_earliest_expiry(
    client,
    owner_headers,
):
    row = _medicine_from_list(client, owner_headers, barcode="LIS10001")
    later = _create_batch(
        client,
        owner_headers,
        row["id"],
        batch_number="LIS-LATER",
        expiry_date=(date.today() + timedelta(days=365)).isoformat(),
        quantity_received=7,
    )
    sooner = _create_batch(
        client,
        owner_headers,
        row["id"],
        batch_number="LIS-SOON",
        expiry_date=(date.today() + timedelta(days=60)).isoformat(),
        quantity_received=4,
    )

    list_row = _medicine_from_list(client, owner_headers, barcode="LIS10001")
    assert list_row["quantity_on_hand"] == 11
    assert list_row["nearest_batch_number"] == sooner["batch_number"]
    assert list_row["nearest_expiry_date"] == sooner["expiry_date"]
    assert list_row["stock_status"] == "low"
    assert later["batch_number"] != list_row["nearest_batch_number"]


def test_list_ignores_void_batches(client, owner_headers, db_session: Session):
    row = _medicine_from_list(client, owner_headers, barcode="ATO20001")
    active = _create_batch(
        client,
        owner_headers,
        row["id"],
        batch_number="ATO-ACTIVE",
        quantity_received=8,
    )
    void_batch = db_session.get(Batch, active["id"])
    assert void_batch is not None

    void_only = Batch(
        medicine_id=row["id"],
        batch_number="ATO-VOID",
        expiry_date=date.today() + timedelta(days=90),
        cost_price=5,
        selling_price=10,
        quantity_on_hand=50,
        quantity_received=50,
        status="void",
    )
    db_session.add(void_only)
    db_session.commit()

    list_row = _medicine_from_list(client, owner_headers, barcode="ATO20001")
    assert list_row["quantity_on_hand"] == 8
    assert list_row["nearest_batch_number"] == active["batch_number"]
