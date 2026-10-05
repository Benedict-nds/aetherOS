from fastapi import APIRouter, Depends, status
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
from app.modules.sales.schemas import SaleCreate
from app.modules.sales.service import create_sale_record

router = APIRouter()

record_sale_access = require_roles(ROLE_OWNER, ROLE_ADMIN, ROLE_PHARMACIST, ROLE_STAFF)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_sale(
    payload: SaleCreate,
    current_user: User = Depends(record_sale_access),
    db: Session = Depends(get_db),
):
    sale = create_sale_record(db, current_user, payload)
    return success_response(data=sale, message="Sale recorded")
