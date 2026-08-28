from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.responses import success_response
from app.core.security import get_current_user
from app.models.user import User
from app.modules.dashboard.service import get_dashboard_summary

router = APIRouter()


@router.get("/summary")
def dashboard_summary(
    _current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    summary = get_dashboard_summary(db)
    return success_response(
        data=summary.model_dump(),
        message="Dashboard summary retrieved",
    )
