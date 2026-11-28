from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.permissions import ROLE_ADMIN, ROLE_OWNER, ROLE_PHARMACIST, require_roles
from app.core.responses import success_response
from app.models.user import User
from app.modules.refunds.schemas import RefundCreate
from app.modules.refunds.service import create_refund_record

router = APIRouter()
create_refund_access = require_roles(ROLE_OWNER, ROLE_ADMIN, ROLE_PHARMACIST)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_refund(
    payload: RefundCreate,
    current_user: User = Depends(create_refund_access),
    db: Session = Depends(get_db),
):
    refund = create_refund_record(db, current_user, payload)
    return success_response(data=refund, message="Refund recorded")
