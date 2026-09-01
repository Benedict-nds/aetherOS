from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.permissions import ROLE_ADMIN, ROLE_OWNER, require_roles
from app.core.responses import success_response
from app.models.user import User
from app.modules.users.schemas import UserCreate, UserUpdate
from app.modules.users.service import (
    create_user_record,
    deactivate_user_record,
    get_user_record,
    list_role_records,
    list_user_records,
    reactivate_user_record,
    update_user_record,
)

router = APIRouter()

manage_users = require_roles(ROLE_OWNER, ROLE_ADMIN)


@router.get("")
def list_users(
    include_inactive: bool = Query(default=True),
    current_user: User = Depends(manage_users),
    db: Session = Depends(get_db),
):
    users = list_user_records(db)
    if not include_inactive:
        users = [user for user in users if user["status"] == "active"]
    return success_response(data=users, message="Users retrieved")


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    current_user: User = Depends(manage_users),
    db: Session = Depends(get_db),
):
    user = create_user_record(db, current_user, payload)
    return success_response(data=user, message="User created")


@router.get("/roles")
def list_assignable_roles(
    current_user: User = Depends(manage_users),
    db: Session = Depends(get_db),
):
    roles = list_role_records(db, current_user)
    return success_response(data=roles, message="Roles retrieved")


@router.get("/{user_id}")
def get_user(
    user_id: int,
    current_user: User = Depends(manage_users),
    db: Session = Depends(get_db),
):
    user = get_user_record(db, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return success_response(data=user, message="User retrieved")


@router.patch("/{user_id}")
def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: User = Depends(manage_users),
    db: Session = Depends(get_db),
):
    user = update_user_record(db, current_user, user_id, payload)
    return success_response(data=user, message="User updated")


@router.delete("/{user_id}")
def deactivate_user(
    user_id: int,
    current_user: User = Depends(manage_users),
    db: Session = Depends(get_db),
):
    deactivate_user_record(db, current_user, user_id)
    return success_response(data=None, message="User deactivated")


@router.post("/{user_id}/reactivate")
def reactivate_user(
    user_id: int,
    current_user: User = Depends(manage_users),
    db: Session = Depends(get_db),
):
    user = reactivate_user_record(db, current_user, user_id)
    return success_response(data=user, message="User reactivated")
