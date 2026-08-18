from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User
from app.modules.auth.repository import get_user_by_email

DEMO_USER = {
    "full_name": "Pharmacy Admin",
    "email": "admin@aetherqore.local",
    "username": "admin",
    "password": "Admin123!",
    "role_name": "owner",
}


def seed_demo_user(db: Session) -> None:
    if get_user_by_email(db, DEMO_USER["email"]) is not None:
        return

    role = db.scalar(
        select(Role).where(Role.name == DEMO_USER["role_name"])
    )

    if role is None:
        raise RuntimeError(
            f"Role '{DEMO_USER['role_name']}' not found; run migrations first"
        )

    db.add(
        User(
            full_name=DEMO_USER["full_name"],
            email=DEMO_USER["email"],
            username=DEMO_USER["username"],
            password_hash=hash_password(DEMO_USER["password"]),
            role_id=role.id,
            status="active",
        )
    )
    db.commit()
