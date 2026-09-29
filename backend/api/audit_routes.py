"""Audit Log API endpoints."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from auth.dependencies import require_admin
from auth.models import User
from db import get_db
from db.repositories import AuditRepository

import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/v1/admin/audit", tags=["audit"])


@router.get("/logs")
async def get_audit_logs(
    limit: int = Query(100, ge=1, le=1000),
    entity: Optional[str] = None,
    action: Optional[str] = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get recent audit logs (admin only)."""
    repo = AuditRepository(db)
    logs = repo.list_recent(limit=limit, entity=entity, action=action)
    return {
        "items": [log.to_dict() for log in logs],
        "count": len(logs),
    }


@router.get("/stats")
async def get_audit_stats(
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get audit statistics (admin only)."""
    from sqlalchemy import select, func
    from db.models.audit import AuditLog

    # By action
    action_stmt = (
        select(AuditLog.action, func.count(AuditLog.id))
        .group_by(AuditLog.action)
    )
    actions = dict(db.execute(action_stmt).all())

    # By entity
    entity_stmt = (
        select(AuditLog.entity, func.count(AuditLog.id))
        .group_by(AuditLog.entity)
    )
    entities = dict(db.execute(entity_stmt).all())

    # Total
    total = db.query(func.count(AuditLog.id)).scalar() or 0

    return {
        "total": total,
        "by_action": actions,
        "by_entity": entities,
    }
