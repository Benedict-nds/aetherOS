from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User
from app.modules.auth.repository import get_user_by_email


def seed_demo_user(db: Session) -> None:
    if get_user_by_email(db, settings.demo_email) is not None:
        return

    role = db.scalar(
        select(Role).where(Role.name == settings.demo_role)
    )

    if role is None:
        raise RuntimeError(
            f"Role '{settings.demo_role}' not found; run migrations first"
        )

    db.add(
        User(
            full_name=settings.demo_full_name,
            email=settings.demo_email,
            username=settings.demo_username,
            password_hash=hash_password(settings.demo_password),
            role_id=role.id,
            status="active",
        )
    )
    db.commit()
