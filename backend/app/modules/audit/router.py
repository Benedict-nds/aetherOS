from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.responses import success_response
from app.core.security import get_current_user
from app.models.user import User
from app.modules.audit.schemas import AuditLogListResponse, AuditLogResponse
from app.modules.audit.service import get_audit_logs

router = APIRouter()


@router.get("/logs")
def list_audit_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: int | None = Query(default=None),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
):
    # RBAC permission dependency can be added here in a future issue.
    logs, total = get_audit_logs(
        db,
        limit=limit,
        offset=offset,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
    )

    payload = AuditLogListResponse(
        items=[AuditLogResponse.model_validate(log) for log in logs],
        total=total,
        limit=limit,
        offset=offset,
    )

    return success_response(
        data=payload.model_dump(),
        message="Audit logs retrieved",
    )
