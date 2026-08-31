from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.permissions import (
    ROLE_ADMIN,
    ROLE_OWNER,
    SYSTEM_ROLES,
    USER_STATUSES,
    can_assign_role,
    can_modify_user,
    get_role_rank,
)
from app.core.security import hash_password
from app.models.user import User
from app.modules.audit.service import (
    ACTION_CREATE,
    ACTION_DEACTIVATE,
    ACTION_REACTIVATE,
    ACTION_UPDATE,
    ENTITY_TYPE_USER,
    create_audit_log,
)
from app.modules.users import repository
from app.modules.users.schemas import UserCreate, UserResponse, UserUpdate


def serialize_user(user: User) -> dict:
    return UserResponse(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        username=user.username,
        role=user.role.name,
        status=user.status,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat(),
    ).model_dump()


def _audit_details(user: User, role_name: str, **extra) -> dict:
    """Safe metadata for user audit events. Never includes credentials."""
    details = {
        "username": user.username,
        "email": user.email,
        "role": role_name,
        "status": user.status,
    }
    details.update(extra)
    return details


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _normalize_username(username: str) -> str:
    return username.strip().lower()


def _get_assignable_role(db: Session, role_name: str):
    normalized = role_name.strip().lower()
    if normalized not in SYSTEM_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid role",
        )

    role = repository.get_role_by_name(db, normalized)
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid role",
        )
    return role


def list_user_records(db: Session) -> list[dict]:
    users = repository.list_users(db)
    return [serialize_user(user) for user in users]


def get_user_record(db: Session, user_id: int) -> dict | None:
    user = repository.get_user_by_id(db, user_id)
    if user is None:
        return None
    return serialize_user(user)


def create_user_record(
    db: Session,
    actor: User,
    payload: UserCreate,
    *,
    ip_address: str | None = None,
) -> dict:
    email = _normalize_email(str(payload.email))
    username = _normalize_username(payload.username)

    if repository.get_user_by_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )

    if repository.get_user_by_username(db, username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    role = _get_assignable_role(db, payload.role)
    if not can_assign_role(actor, role.name):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot assign this role",
        )

    user = User(
        full_name=payload.full_name.strip(),
        email=email,
        username=username,
        password_hash=hash_password(payload.password),
        role_id=role.id,
        status="active",
    )

    try:
        saved = repository.save_user(db, user)
        user_id = saved.id
        create_audit_log(
            db,
            user=actor,
            action=ACTION_CREATE,
            entity_type=ENTITY_TYPE_USER,
            entity_id=user_id,
            details=_audit_details(saved, role.name),
            ip_address=ip_address,
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User conflicts with an existing record",
        ) from exc

    refreshed = repository.get_user_by_id(db, user_id)
    return serialize_user(refreshed)


def _apply_user_update(
    db: Session,
    actor: User,
    user_id: int,
    payload: UserUpdate,
    *,
    action: str,
    ip_address: str | None,
) -> dict:
    user = repository.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not can_modify_user(actor, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to modify this user",
        )

    updates = payload.model_dump(exclude_unset=True)

    if "status" in updates:
        if updates["status"] not in USER_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid user status",
            )
        if user.id == actor.id and updates["status"] == "inactive":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot deactivate your own account",
            )

    if "email" in updates and updates["email"] is not None:
        email = _normalize_email(str(updates["email"]))
        existing = repository.get_user_by_email(db, email)
        if existing and existing.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already exists",
            )
        user.email = email

    if "username" in updates and updates["username"] is not None:
        username = _normalize_username(updates["username"])
        existing = repository.get_user_by_username(db, username)
        if existing and existing.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already exists",
            )
        user.username = username

    if "full_name" in updates and updates["full_name"] is not None:
        user.full_name = updates["full_name"].strip()

    if "password" in updates and updates["password"] is not None:
        user.password_hash = hash_password(updates["password"])

    if "role" in updates and updates["role"] is not None:
        role = _get_assignable_role(db, updates["role"])
        if not can_assign_role(actor, role.name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot assign this role",
            )
        if user.role.name == ROLE_OWNER and actor.role.name != ROLE_OWNER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to modify this user",
            )
        user.role_id = role.id

    if "status" in updates and updates["status"] is not None:
        user.status = updates["status"]

    user.updated_at = datetime.now(timezone.utc)

    try:
        repository.update_user(db, user)
        create_audit_log(
            db,
            user=actor,
            action=action,
            entity_type=ENTITY_TYPE_USER,
            entity_id=user.id,
            # Field names only: the password value is never recorded.
            details=_audit_details(
                user,
                user.role.name,
                changed_fields=sorted(updates.keys()),
            ),
            ip_address=ip_address,
        )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User conflicts with an existing record",
        ) from exc

    refreshed = repository.get_user_by_id(db, user_id)
    return serialize_user(refreshed)


def update_user_record(
    db: Session,
    actor: User,
    user_id: int,
    payload: UserUpdate,
    *,
    ip_address: str | None = None,
) -> dict:
    return _apply_user_update(
        db,
        actor,
        user_id,
        payload,
        action=ACTION_UPDATE,
        ip_address=ip_address,
    )


def deactivate_user_record(
    db: Session,
    actor: User,
    user_id: int,
    *,
    ip_address: str | None = None,
) -> None:
    user = repository.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.id == actor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot deactivate your own account",
        )

    if not can_modify_user(actor, user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to modify this user",
        )

    user.status = "inactive"
    user.updated_at = datetime.now(timezone.utc)
    repository.update_user(db, user)
    create_audit_log(
        db,
        user=actor,
        action=ACTION_DEACTIVATE,
        entity_type=ENTITY_TYPE_USER,
        entity_id=user.id,
        details=_audit_details(user, user.role.name),
        ip_address=ip_address,
    )
    db.commit()


def reactivate_user_record(
    db: Session,
    actor: User,
    user_id: int,
    *,
    ip_address: str | None = None,
) -> dict:
    return _apply_user_update(
        db,
        actor,
        user_id,
        UserUpdate(status="active"),
        action=ACTION_REACTIVATE,
        ip_address=ip_address,
    )


def list_role_records(db: Session, actor: User) -> list[dict]:
    actor_rank = get_role_rank(actor.role.name)
    roles = repository.list_roles(db)
    assignable = [
        role
        for role in roles
        if actor_rank is not None
        and get_role_rank(role.name) is not None
        and get_role_rank(role.name).value <= actor_rank.value
        and not (actor.role.name == ROLE_ADMIN and role.name == ROLE_OWNER)
    ]
    return [
        {
            "id": role.id,
            "name": role.name,
            "description": role.description,
        }
        for role in assignable
    ]
