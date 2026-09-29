"""Report Repository."""
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from db.models.report import Report


class ReportRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> Report:
        report = Report(**kwargs)
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_by_id(self, report_id: str) -> Optional[Report]:
        return self.db.query(Report).filter(Report.id == report_id).first()

    def list_recent(
        self,
        limit: int = 100,
        status: Optional[str] = None,
        priority: Optional[str] = None,
        assigned_to: Optional[str] = None,
        type_: Optional[str] = None,
    ) -> list[Report]:
        q = self.db.query(Report).order_by(Report.created_at.desc())
        if status:
            q = q.filter(Report.status == status)
        if priority:
            q = q.filter(Report.priority == priority)
        if assigned_to:
            q = q.filter(Report.assigned_to == assigned_to)
        if type_:
            q = q.filter(Report.type == type_)
        return q.limit(limit).all()

    def list_overdue(self) -> list[Report]:
        """Reports past SLA deadline."""
        return self.db.query(Report).filter(
            Report.sla_deadline < datetime.utcnow(),
            Report.status.in_(["pending", "assigned", "in_progress"]),
        ).all()

    def assign(self, report_id: str, member_id: str) -> Optional[Report]:
        report = self.get_by_id(report_id)
        if not report:
            return None
        report.assigned_to = member_id
        report.assigned_at = datetime.utcnow()
        report.status = "assigned"
        self.db.commit()
        self.db.refresh(report)
        return report

    def update_status(self, report_id: str, status: str, **fields) -> Optional[Report]:
        report = self.get_by_id(report_id)
        if not report:
            return None
        report.status = status
        for key, value in fields.items():
            if hasattr(report, key):
                setattr(report, key, value)
        if status == "resolved":
            report.resolved_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(report)
        return report

    def stats(self) -> dict:
        q = self.db.query(Report)
        total = q.count()
        by_status = dict(
            self.db.query(Report.status, func.count(Report.id))
            .group_by(Report.status).all()
        )
        by_priority = dict(
            self.db.query(Report.priority, func.count(Report.id))
            .group_by(Report.priority).all()
        )
        by_type = dict(
            self.db.query(Report.type, func.count(Report.id))
            .group_by(Report.type).all()
        )
        return {
            "total": total,
            "by_status": by_status,
            "by_priority": by_priority,
            "by_type": by_type,
        }
