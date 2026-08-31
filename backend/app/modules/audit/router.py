from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.permissions import ROLE_ADMIN, ROLE_OWNER, require_roles
from app.core.responses import success_response
from app.models.user import User
from app.modules.audit.schemas import AuditLogListResponse, AuditLogResponse
from app.modules.audit.service import get_audit_logs

router = APIRouter()

view_audit_logs = require_roles(ROLE_OWNER, ROLE_ADMIN)


@router.get("/logs")
def list_audit_logs(
    current_user: User = Depends(view_audit_logs),
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user_id: int | None = Query(default=None),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
):
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
