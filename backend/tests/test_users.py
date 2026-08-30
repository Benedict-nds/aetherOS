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


@pytest.fixture
def staff_headers(client, db_session: Session):
    role = db_session.scalar(select(Role).where(Role.name == "staff"))
    if role is None:
        role = db_session.scalar(select(Role).where(Role.name == "cashier"))
    assert role is not None
    user = User(
        full_name="Staff User",
        email="staff.user@aetherqore.local",
        username="staffuser",
        password_hash=hash_password("StaffPass123!"),
        role_id=role.id,
        status="active",
    )
    db_session.add(user)
    db_session.commit()
    return _login(client, "staff.user@aetherqore.local", "StaffPass123!")


def test_staff_cannot_list_users(client, staff_headers):
    response = client.get("/api/users", headers=staff_headers)
    assert response.status_code == 403
    assert response.json()["message"] == "Insufficient permissions"


def test_owner_can_create_list_and_get_user(client, owner_headers):
    create_response = client.post(
        "/api/users",
        headers=owner_headers,
        json={
            "full_name": "Jane Pharmacist",
            "email": "jane.pharmacist@aetherqore.local",
            "username": "janepharma",
            "password": "SecurePass123!",
            "role": "pharmacist",
        },
    )
    assert create_response.status_code == 201
    created = create_response.json()["data"]
    assert created["role"] == "pharmacist"
    assert "password_hash" not in created

    user_id = created["id"]
    list_response = client.get("/api/users", headers=owner_headers)
    assert list_response.status_code == 200
    assert any(user["email"] == "jane.pharmacist@aetherqore.local" for user in list_response.json()["data"])

    get_response = client.get(f"/api/users/{user_id}", headers=owner_headers)
    assert get_response.status_code == 200
    assert get_response.json()["data"]["username"] == "janepharma"


def test_duplicate_email_rejected(client, owner_headers):
    payload = {
        "full_name": "Duplicate Email",
        "email": "duplicate@aetherqore.local",
        "username": "duplicate1",
        "password": "SecurePass123!",
        "role": "staff",
    }
    assert client.post("/api/users", headers=owner_headers, json=payload).status_code == 201
    response = client.post(
        "/api/users",
        headers=owner_headers,
        json={**payload, "username": "duplicate2"},
    )
    assert response.status_code == 409
    assert response.json()["message"] == "Email already exists"


def test_invalid_role_rejected(client, owner_headers):
    response = client.post(
        "/api/users",
        headers=owner_headers,
        json={
            "full_name": "Bad Role",
            "email": "badrole@aetherqore.local",
            "username": "badrole",
            "password": "SecurePass123!",
            "role": "superadmin",
        },
    )
    assert response.status_code == 422
    assert response.json()["message"] == "Invalid role"


def test_deactivate_and_reactivate_user(client, owner_headers):
    create_response = client.post(
        "/api/users",
        headers=owner_headers,
        json={
            "full_name": "Temp Staff",
            "email": "temp.staff@aetherqore.local",
            "username": "tempstaff",
            "password": "SecurePass123!",
            "role": "staff",
        },
    )
    user_id = create_response.json()["data"]["id"]

    delete_response = client.delete(f"/api/users/{user_id}", headers=owner_headers)
    assert delete_response.status_code == 200

    login_response = client.post(
        "/api/auth/login",
        json={"email": "temp.staff@aetherqore.local", "password": "SecurePass123!"},
    )
    assert login_response.status_code == 401

    reactivate_response = client.post(
        f"/api/users/{user_id}/reactivate",
        headers=owner_headers,
    )
    assert reactivate_response.status_code == 200
    assert reactivate_response.json()["data"]["status"] == "active"

    login_response = client.post(
        "/api/auth/login",
        json={"email": "temp.staff@aetherqore.local", "password": "SecurePass123!"},
    )
    assert login_response.status_code == 200


def test_owner_cannot_deactivate_self(client, owner_headers, db_session: Session):
    owner = db_session.scalar(select(User).where(User.email == settings.demo_email))
    response = client.delete(f"/api/users/{owner.id}", headers=owner_headers)
    assert response.status_code == 403
    assert response.json()["message"] == "You cannot deactivate your own account"


def test_list_assignable_roles(client, owner_headers):
    response = client.get("/api/users/roles", headers=owner_headers)
    assert response.status_code == 200
    role_names = {role["name"] for role in response.json()["data"]}
    assert role_names == {"owner", "admin", "pharmacist", "staff"}
