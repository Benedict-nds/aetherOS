from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.permissions import ROLE_ADMIN, ROLE_OWNER, ROLE_PHARMACIST, ROLE_STAFF, require_roles
from app.core.responses import success_response
from app.models.user import User
from app.modules.dashboard.service import get_dashboard_summary

router = APIRouter()

dashboard_access = require_roles(ROLE_OWNER, ROLE_ADMIN, ROLE_PHARMACIST, ROLE_STAFF)


@router.get("/summary")
def dashboard_summary(
    _current_user: User = Depends(dashboard_access),
    db: Session = Depends(get_db),
):
    summary = get_dashboard_summary(db)
    return success_response(
        data=summary.model_dump(),
        message="Dashboard summary retrieved",
    )
