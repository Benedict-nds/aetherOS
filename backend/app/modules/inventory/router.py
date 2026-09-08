from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.permissions import (
    ROLE_ADMIN,
    ROLE_OWNER,
    ROLE_PHARMACIST,
    ROLE_STAFF,
    require_roles,
)
from app.core.responses import success_response
from app.models.user import User
from app.modules.audit.service import resolve_client_ip
from app.modules.inventory.schemas import MedicineCategoryCreate, MedicineCreate, MedicineUpdate
from app.modules.inventory.service import (
    create_category_record,
    create_medicine_record,
    get_medicine_record,
    list_category_records,
    list_medicine_records,
    update_medicine_record,
)

medicines_router = APIRouter()
categories_router = APIRouter()

read_medicines = require_roles(ROLE_OWNER, ROLE_ADMIN, ROLE_PHARMACIST, ROLE_STAFF)
manage_medicines = require_roles(ROLE_OWNER, ROLE_ADMIN, ROLE_PHARMACIST)
manage_categories = require_roles(ROLE_OWNER, ROLE_ADMIN)


@medicines_router.get("")
def list_medicines(
    q: str | None = Query(default=None),
    category_id: int | None = Query(default=None),
    is_active: bool = Query(default=True),
    current_user: User = Depends(read_medicines),
    db: Session = Depends(get_db),
):
    medicines = list_medicine_records(
        db,
        q=q,
        category_id=category_id,
        is_active=is_active,
    )
    return success_response(data=medicines, message="Medicines retrieved")


@medicines_router.post("", status_code=status.HTTP_201_CREATED)
def create_medicine(
    payload: MedicineCreate,
    request: Request,
    current_user: User = Depends(manage_medicines),
    db: Session = Depends(get_db),
):
    medicine = create_medicine_record(
        db,
        current_user,
        payload,
        ip_address=resolve_client_ip(request),
    )
    return success_response(data=medicine, message="Medicine created")


@medicines_router.get("/{medicine_id}")
def get_medicine(
    medicine_id: int,
    current_user: User = Depends(read_medicines),
    db: Session = Depends(get_db),
):
    medicine = get_medicine_record(db, medicine_id)
    if medicine is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medicine not found")
    return success_response(data=medicine, message="Medicine retrieved")


@medicines_router.patch("/{medicine_id}")
def update_medicine(
    medicine_id: int,
    payload: MedicineUpdate,
    request: Request,
    current_user: User = Depends(manage_medicines),
    db: Session = Depends(get_db),
):
    medicine = update_medicine_record(
        db,
        current_user,
        medicine_id,
        payload,
        ip_address=resolve_client_ip(request),
    )
    return success_response(data=medicine, message="Medicine updated")


@categories_router.get("")
def list_medicine_categories(
    current_user: User = Depends(read_medicines),
    db: Session = Depends(get_db),
):
    categories = list_category_records(db)
    return success_response(data=categories, message="Medicine categories retrieved")


@categories_router.post("", status_code=status.HTTP_201_CREATED)
def create_medicine_category(
    payload: MedicineCategoryCreate,
    current_user: User = Depends(manage_categories),
    db: Session = Depends(get_db),
):
    category = create_category_record(db, payload)
    return success_response(data=category, message="Medicine category created")
