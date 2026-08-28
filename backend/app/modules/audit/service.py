from datetime import datetime, timezone

from fastapi import Request
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User
from app.modules.audit.repository import fetch_audit_logs, insert_audit_log

ACTION_LOGIN = "LOGIN"
ACTION_LOGOUT = "LOGOUT"
ACTION_CREATE = "CREATE"
ACTION_UPDATE = "UPDATE"
ACTION_DELETE = "DELETE"
ACTION_VIEW = "VIEW"

ENTITY_TYPE_AUTH = "auth"

_SENSITIVE_DETAIL_KEYS = frozenset(
    {
        "password",
        "password_hash",
        "access_token",
        "token",
        "authorization",
        "secret",
        "secret_key",
        "credentials",
    }
)


def resolve_client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    if request.client:
        return request.client.host

    return None


def _sanitize_details(details: dict | None) -> dict | None:
    if not details:
        return None

    sanitized = {
        key: value
        for key, value in details.items()
        if key.lower() not in _SENSITIVE_DETAIL_KEYS
    }

    return sanitized or None


def create_audit_log(
    db: Session,
    *,
    action: str,
    entity_type: str,
    user: User | None = None,
    entity_id: int | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
    commit: bool = False,
) -> AuditLog:
    audit_log = AuditLog(
        user_id=user.id if user is not None else None,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=_sanitize_details(details),
        ip_address=ip_address,
        created_at=datetime.now(timezone.utc),
    )

    created = insert_audit_log(db, audit_log)

    if commit:
        db.commit()
        db.refresh(created)

    return created


def get_audit_logs(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    user_id: int | None = None,
    action: str | None = None,
    entity_type: str | None = None,
) -> tuple[list[AuditLog], int]:
    return fetch_audit_logs(
        db,
        limit=limit,
        offset=offset,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
    )
