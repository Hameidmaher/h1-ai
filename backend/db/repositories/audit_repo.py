"""Audit log repository."""
from typing import List, Optional
import json

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from db.models.audit import AuditLog


class AuditRepository:
    """CRUD for audit logs."""

    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        user_id: str,
        username: str,
        action: str,
        entity: str,
        entity_id: str = "",
        details: Optional[dict] = None,
        ip_address: str = "",
        user_agent: str = "",
    ) -> AuditLog:
        entry = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            entity=entity,
            entity_id=entity_id,
            details=json.dumps(details or {}, ensure_ascii=False),
            ip_address=ip_address,
            user_agent=user_agent[:300],
        )
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def list_recent(
        self,
        limit: int = 100,
        entity: Optional[str] = None,
        action: Optional[str] = None,
    ) -> List[AuditLog]:
        stmt = select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
        if entity:
            stmt = stmt.where(AuditLog.entity == entity)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        return list(self.db.execute(stmt).scalars().all())

    def count(self) -> int:
        stmt = select(func.count(AuditLog.id))
        return self.db.execute(stmt).scalar() or 0
