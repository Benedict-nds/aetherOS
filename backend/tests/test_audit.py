from sqlalchemy import select

from app.core.config import settings
from app.core.db import SessionLocal
from app.models.audit_log import AuditLog
from app.modules.audit.service import (
    ACTION_CREATE,
    ACTION_LOGIN,
    ACTION_LOGOUT,
    ENTITY_TYPE_AUTH,
    create_audit_log,
)


def _auth_headers(client) -> dict[str, str]:
    login_response = client.post(
        "/api/auth/login",
        json={
            "email": settings.demo_email,
            "password": settings.demo_password,
        },
    )
    token = login_response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _latest_audit_log(
    *,
    action: str | None = None,
    entity_type: str | None = None,
    user_id: int | None = None,
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

        return db.scalar(query.limit(1))
    finally:
        db.close()


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
    assert audit_log.details is None or "password" not in audit_log.details
    assert audit_log.details is None or "access_token" not in audit_log.details


def test_logout_creates_audit_event(client):
    headers = _auth_headers(client)

    response = client.post(
        "/api/auth/logout",
        headers=headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True

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
    assert body["message"] == "Authentication required"
    assert body["errors"] == []


def test_audit_logs_authenticated(client):
    response = client.get(
        "/api/audit/logs",
        headers=_auth_headers(client),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "Audit logs retrieved"

    data = body["data"]
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert isinstance(data["items"], list)
    assert data["total"] >= 1

    first_item = data["items"][0]
    assert "id" in first_item
    assert "user_id" in first_item
    assert "action" in first_item
    assert "entity_type" in first_item
    assert "entity_id" in first_item
    assert "details" in first_item
    assert "ip_address" in first_item
    assert "created_at" in first_item
    assert "password_hash" not in first_item


def test_audit_logs_pagination_and_filters(client):
    headers = _auth_headers(client)

    response = client.get(
        "/api/audit/logs",
        headers=headers,
        params={
            "limit": 1,
            "offset": 0,
            "action": ACTION_LOGIN,
            "entity_type": ENTITY_TYPE_AUTH,
        },
    )

    assert response.status_code == 200
    body = response.json()
    data = body["data"]

    assert data["limit"] == 1
    assert data["offset"] == 0
    assert len(data["items"]) <= 1

    for item in data["items"]:
        assert item["action"] == ACTION_LOGIN
        assert item["entity_type"] == ENTITY_TYPE_AUTH


def test_audit_details_do_not_store_sensitive_values():
    db = SessionLocal()
    try:
        audit_log = create_audit_log(
            db,
            action=ACTION_CREATE,
            entity_type="user",
            details={
                "username": "admin",
                "password": "Admin123!",
                "access_token": "secret-token",
            },
            commit=True,
        )

        assert audit_log.details == {"username": "admin"}
        assert "password" not in (audit_log.details or {})
        assert "access_token" not in (audit_log.details or {})
    finally:
        db.close()
