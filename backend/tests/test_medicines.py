import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
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
