import json
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import SessionLocal
from app.core.security import hash_password
from app.models.audit_log import AuditLog
from app.models.role import Role
from app.models.user import User
from app.modules.audit.service import (
    ACTION_CREATE,
    ACTION_DEACTIVATE,
    ACTION_LOGIN,
    ACTION_LOGOUT,
    ACTION_REACTIVATE,
    ACTION_UPDATE,
    ENTITY_TYPE_AUTH,
    ENTITY_TYPE_USER,
    create_audit_log,
)

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
    assert role is not None, f"role {role_name} missing"

    user = User(
        full_name=f"Audit {role_name.title()}",
        email=email,
        username=username,
        password_hash=hash_password(FIXTURE_PASSWORD),
        role_id=role.id,
        status="active",
    )
    db.add(user)
    db.commit()
    return user


def _latest_audit_log(
    *,
    action: str | None = None,
    entity_type: str | None = None,
    user_id: int | None = None,
    entity_id: int | None = None,
) -> AuditLog | None:
    db = SessionLocal()
    try:
        query = select(AuditLog).order_by(AuditLog.id.desc())

        if action is not None:
            query = query.where(AuditLog.action == action)
        if entity_type is not None:
            query = query.where(AuditLog.entity_type == entity_type)
        if user_id is not None:
            query = query.where(AuditLog.user_id == user_id)
        if entity_id is not None:
            query = query.where(AuditLog.entity_id == entity_id)

        return db.scalar(query.limit(1))
    finally:
        db.close()


@pytest.fixture
def owner_headers(client):
    return _login(client, settings.demo_email, settings.demo_password)


@pytest.fixture
def admin_headers(client, db_session: Session):
    _ensure_user(db_session, "admin", "audit.admin@example.com", "auditadmin")
    return _login(client, "audit.admin@example.com", FIXTURE_PASSWORD)


@pytest.fixture
def pharmacist_headers(client, db_session: Session):
    _ensure_user(
        db_session,
        "pharmacist",
        "audit.pharmacist@example.com",
        "auditpharmacist",
    )
    return _login(client, "audit.pharmacist@example.com", FIXTURE_PASSWORD)


@pytest.fixture
def staff_headers(client, db_session: Session):
    _ensure_user(db_session, "staff", "audit.staff@example.com", "auditstaff")
    return _login(client, "audit.staff@example.com", FIXTURE_PASSWORD)


def _create_user(client, headers, *, role: str = "staff") -> dict:
    suffix = uuid4().hex[:10]
    response = client.post(
        "/api/users",
        headers=headers,
        json={
            "full_name": "Audit Target",
            "email": f"target.{suffix}@example.com",
            "username": f"target{suffix}",
            "password": "TargetPass123!",
            "role": role,
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


def test_create_audit_log_persists():
    db = SessionLocal()
    try:
        audit_log = create_audit_log(
            db,
            action=ACTION_CREATE,
            entity_type="medicine",
            entity_id=42,
            details={"name": "Paracetamol"},
            ip_address="127.0.0.1",
            commit=True,
        )

        persisted = db.get(AuditLog, audit_log.id)
        assert persisted is not None
        assert persisted.action == ACTION_CREATE
        assert persisted.entity_type == "medicine"
        assert persisted.entity_id == 42
        assert persisted.details == {"name": "Paracetamol"}
        assert persisted.ip_address == "127.0.0.1"
        assert persisted.created_at is not None
    finally:
        db.close()


def test_login_creates_audit_event(client):
    response = client.post(
        "/api/auth/login",
        json={
            "email": settings.demo_email,
            "password": settings.demo_password,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True

    user_id = body["data"]["user"]["id"]
    audit_log = _latest_audit_log(
        action=ACTION_LOGIN,
        entity_type=ENTITY_TYPE_AUTH,
        user_id=user_id,
    )

    assert audit_log is not None
    assert audit_log.user_id == user_id
    assert audit_log.action == ACTION_LOGIN
    assert audit_log.entity_type == ENTITY_TYPE_AUTH
    assert settings.demo_password not in json.dumps(audit_log.details or {})


def test_logout_creates_audit_event(client, owner_headers):
    response = client.post("/api/auth/logout", headers=owner_headers)

    assert response.status_code == 200
    assert response.json()["success"] is True

    audit_log = _latest_audit_log(
        action=ACTION_LOGOUT,
        entity_type=ENTITY_TYPE_AUTH,
    )

    assert audit_log is not None
    assert audit_log.action == ACTION_LOGOUT
    assert audit_log.entity_type == ENTITY_TYPE_AUTH
    assert audit_log.user_id is not None


def test_audit_logs_requires_auth(client):
    response = client.get("/api/audit/logs")

    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["data"] is None
    assert body["message"] == "Authentication required"
    assert body["errors"] == []


def test_staff_cannot_view_audit_logs(client, staff_headers):
    response = client.get("/api/audit/logs", headers=staff_headers)

    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["message"] == "Insufficient permissions"


def test_pharmacist_cannot_view_audit_logs(client, pharmacist_headers):
    response = client.get("/api/audit/logs", headers=pharmacist_headers)

    assert response.status_code == 403
    assert response.json()["message"] == "Insufficient permissions"


def test_admin_can_view_audit_logs(client, admin_headers):
    response = client.get("/api/audit/logs", headers=admin_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Audit logs retrieved"
    assert isinstance(body["data"]["items"], list)


def test_owner_can_view_audit_logs(client, owner_headers):
    response = client.get("/api/audit/logs", headers=owner_headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["errors"] == []

    data = body["data"]
    assert data["total"] >= 1
    assert data["limit"] == 50
    assert data["offset"] == 0

    first_item = data["items"][0]
    assert set(first_item) == {
        "id",
        "user_id",
        "action",
        "entity_type",
        "entity_id",
        "details",
        "ip_address",
        "created_at",
    }
    assert "password_hash" not in first_item


def test_audit_logs_pagination(client, owner_headers):
    first_page = client.get(
        "/api/audit/logs",
        headers=owner_headers,
        params={"limit": 1, "offset": 0},
    )
    second_page = client.get(
        "/api/audit/logs",
        headers=owner_headers,
        params={"limit": 1, "offset": 1},
    )

    assert first_page.status_code == 200
    assert second_page.status_code == 200

    first_data = first_page.json()["data"]
    second_data = second_page.json()["data"]

    assert first_data["limit"] == 1
    assert second_data["offset"] == 1
    assert len(first_data["items"]) == 1
    assert len(second_data["items"]) == 1
    assert first_data["total"] == second_data["total"]
    assert first_data["items"][0]["id"] != second_data["items"][0]["id"]


def test_audit_logs_rejects_out_of_range_limit(client, owner_headers):
    response = client.get(
        "/api/audit/logs",
        headers=owner_headers,
        params={"limit": 1000},
    )

    assert response.status_code == 422
    assert response.json()["success"] is False


def test_audit_logs_filters(client, owner_headers):
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": settings.demo_email,
            "password": settings.demo_password,
        },
    )
    owner_id = login_response.json()["data"]["user"]["id"]

    response = client.get(
        "/api/audit/logs",
        headers=owner_headers,
        params={
            "action": ACTION_LOGIN,
            "entity_type": ENTITY_TYPE_AUTH,
            "user_id": owner_id,
        },
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] >= 1

    for item in data["items"]:
        assert item["action"] == ACTION_LOGIN
        assert item["entity_type"] == ENTITY_TYPE_AUTH
        assert item["user_id"] == owner_id

    unmatched = client.get(
        "/api/audit/logs",
        headers=owner_headers,
        params={"action": "NO_SUCH_ACTION"},
    )
    assert unmatched.status_code == 200
    assert unmatched.json()["data"]["total"] == 0
    assert unmatched.json()["data"]["items"] == []


def test_audit_details_do_not_store_sensitive_values():
    db = SessionLocal()
    try:
        audit_log = create_audit_log(
            db,
            action=ACTION_CREATE,
            entity_type=ENTITY_TYPE_USER,
            details={
                "username": "admin",
                "password": "Admin123!",
                "password_hash": "$2b$12$notarealhash",
                "access_token": "secret-token",
                "refresh_token": "secret-refresh",
                "authorization": "Bearer secret",
                "secret_key": "super-secret",
                "nested": {"token": "inner-secret", "role": "owner"},
            },
            commit=True,
        )

        details = audit_log.details or {}
        assert details == {
            "username": "admin",
            "nested": {"role": "owner"},
        }

        serialized = json.dumps(details)
        for leaked in (
            "Admin123!",
            "$2b$12$notarealhash",
            "secret-token",
            "secret-refresh",
            "Bearer secret",
            "super-secret",
            "inner-secret",
        ):
            assert leaked not in serialized
    finally:
        db.close()


def test_create_user_creates_audit_event(client, owner_headers, db_session: Session):
    owner = db_session.scalar(select(User).where(User.email == settings.demo_email))
    created = _create_user(client, owner_headers)

    audit_log = _latest_audit_log(
        action=ACTION_CREATE,
        entity_type=ENTITY_TYPE_USER,
        entity_id=created["id"],
    )

    assert audit_log is not None
    assert audit_log.user_id == owner.id
    assert audit_log.entity_id == created["id"]
    assert audit_log.details["email"] == created["email"]
    assert audit_log.details["username"] == created["username"]
    assert audit_log.details["role"] == "staff"
    assert audit_log.details["status"] == "active"
    assert "TargetPass123!" not in json.dumps(audit_log.details)


def test_update_user_creates_audit_event(client, owner_headers):
    created = _create_user(client, owner_headers)

    response = client.patch(
        f"/api/users/{created['id']}",
        headers=owner_headers,
        json={"full_name": "Renamed Target"},
    )
    assert response.status_code == 200

    audit_log = _latest_audit_log(
        action=ACTION_UPDATE,
        entity_type=ENTITY_TYPE_USER,
        entity_id=created["id"],
    )

    assert audit_log is not None
    assert audit_log.details["changed_fields"] == ["full_name"]
    assert audit_log.details["email"] == created["email"]


def test_deactivate_user_creates_audit_event(client, owner_headers):
    created = _create_user(client, owner_headers)

    response = client.delete(f"/api/users/{created['id']}", headers=owner_headers)
    assert response.status_code == 200

    audit_log = _latest_audit_log(
        action=ACTION_DEACTIVATE,
        entity_type=ENTITY_TYPE_USER,
        entity_id=created["id"],
    )

    assert audit_log is not None
    assert audit_log.details["status"] == "inactive"
    assert audit_log.entity_id == created["id"]


def test_reactivate_user_creates_audit_event(client, owner_headers):
    created = _create_user(client, owner_headers)
    client.delete(f"/api/users/{created['id']}", headers=owner_headers)

    response = client.post(
        f"/api/users/{created['id']}/reactivate",
        headers=owner_headers,
    )
    assert response.status_code == 200

    audit_log = _latest_audit_log(
        action=ACTION_REACTIVATE,
        entity_type=ENTITY_TYPE_USER,
        entity_id=created["id"],
    )

    assert audit_log is not None
    assert audit_log.details["status"] == "active"


def test_password_change_never_appears_in_audit_details(client, owner_headers):
    created = _create_user(client, owner_headers)
    new_password = "RotatedPass456!"

    response = client.patch(
        f"/api/users/{created['id']}",
        headers=owner_headers,
        json={"password": new_password},
    )
    assert response.status_code == 200

    audit_log = _latest_audit_log(
        action=ACTION_UPDATE,
        entity_type=ENTITY_TYPE_USER,
        entity_id=created["id"],
    )

    assert audit_log is not None
    serialized = json.dumps(audit_log.details)
    assert new_password not in serialized
    assert "password" not in audit_log.details
    assert "password_hash" not in audit_log.details
    # The field name is retained so the rotation itself remains auditable.
    assert audit_log.details["changed_fields"] == ["password"]


def test_failed_login_does_not_create_audit_event(client):
    before = _latest_audit_log(action=ACTION_LOGIN)
    before_id = before.id if before else 0

    response = client.post(
        "/api/auth/login",
        json={"email": settings.demo_email, "password": "WrongPassword!"},
    )
    assert response.status_code == 401

    after = _latest_audit_log(action=ACTION_LOGIN)
    after_id = after.id if after else 0
    assert after_id == before_id
