from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.role import Role
from app.models.user import User


def list_users(db: Session, *, include_inactive: bool = True) -> list[User]:
    query = select(User).options(selectinload(User.role)).order_by(User.full_name.asc())
    if not include_inactive:
        query = query.where(User.status == "active")
    return list(db.scalars(query))


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.scalar(
        select(User).options(selectinload(User.role)).where(User.id == user_id)
    )


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(User.email == email))


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def get_role_by_name(db: Session, role_name: str) -> Role | None:
    return db.scalar(select(Role).where(Role.name == role_name))


def get_role_by_id(db: Session, role_id: int) -> Role | None:
    return db.get(Role, role_id)


def list_roles(db: Session) -> list[Role]:
    return list(db.scalars(select(Role).order_by(Role.name.asc())))


def save_user(db: Session, user: User) -> User:
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user: User) -> User:
    db.commit()
    db.refresh(user)
    return user
