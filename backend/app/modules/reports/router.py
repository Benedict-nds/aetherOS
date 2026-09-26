from fastapi import APIRouter, Depends, Query
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
from app.modules.reports.service import get_expiry_report, get_low_stock_report

router = APIRouter()

reports_access = require_roles(ROLE_OWNER, ROLE_ADMIN, ROLE_PHARMACIST, ROLE_STAFF)


@router.get("/low-stock")
def low_stock_report(
    _current_user: User = Depends(reports_access),
    db: Session = Depends(get_db),
):
    rows = get_low_stock_report(db)
    return success_response(data=rows, message="Low stock report retrieved")


@router.get("/expiry")
def expiry_report(
    within_days: int = Query(default=90, ge=1),
    _current_user: User = Depends(reports_access),
    db: Session = Depends(get_db),
):
    rows = get_expiry_report(db, within_days=within_days)
    return success_response(data=rows, message="Expiry report retrieved")
