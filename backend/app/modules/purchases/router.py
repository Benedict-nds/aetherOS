from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.permissions import ROLE_ADMIN, ROLE_OWNER, ROLE_PHARMACIST, require_roles
from app.core.responses import success_response
from app.models.user import User
from app.modules.audit.service import resolve_client_ip
from app.modules.purchases.schemas import ReceiptCreate
from app.modules.purchases.service import create_receipt_record

router = APIRouter()
manage_receipts = require_roles(ROLE_OWNER, ROLE_ADMIN, ROLE_PHARMACIST)


@router.post("/receipts", status_code=status.HTTP_201_CREATED)
def create_receipt(payload: ReceiptCreate, request: Request, current_user: User = Depends(manage_receipts), db: Session = Depends(get_db)):
    receipt = create_receipt_record(db, current_user, payload, ip_address=resolve_client_ip(request))
    return success_response(data={"lines": receipt}, message="Goods receipt created")
