from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(
        select(User).where(User.email == email)
    )


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.scalar(
        select(User).where(User.id == user_id)
    )