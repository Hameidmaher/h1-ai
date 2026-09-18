"""Assignment Repository."""
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from db.models.assignment import Assignment


class AssignmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> Assignment:
        assignment = Assignment(**kwargs)
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment

    def get_by_id(self, aid: str) -> Optional[Assignment]:
        return self.db.query(Assignment).filter(Assignment.id == aid).first()

    def list_by_member(self, member_id: str, status: Optional[str] = None) -> list[Assignment]:
        q = self.db.query(Assignment).filter(Assignment.team_member_id == member_id)
        if status:
            q = q.filter(Assignment.status == status)
        return q.order_by(Assignment.assigned_at.desc()).all()

    def list_by_report(self, report_id: str) -> list[Assignment]:
        return self.db.query(Assignment).filter(
            Assignment.report_id == report_id
        ).order_by(Assignment.assigned_at.desc()).all()

    def update_status(self, aid: str, status: str, **fields) -> Optional[Assignment]:
        a = self.get_by_id(aid)
        if not a:
            return None
        a.status = status
        for key, value in fields.items():
            if hasattr(a, key):
                setattr(a, key, value)
        if status == "completed":
            a.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(a)
        return a

    def count_by_member(self, member_id: str) -> int:
        return self.db.query(Assignment).filter(
            Assignment.team_member_id == member_id,
            Assignment.status.in_(["assigned", "in_progress"]),
        ).count()
