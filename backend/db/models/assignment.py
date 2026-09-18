"""Assignment — links a report to a team member."""
from sqlalchemy import Column, String, Text, DateTime, JSON, Index, ForeignKey, Integer
from sqlalchemy.sql import func
from db.base import Base


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(String(36), primary_key=True)
    report_id = Column(String(36), ForeignKey("reports.id"), nullable=False, index=True)
    team_member_id = Column(String(36), ForeignKey("team_members.id"), nullable=False, index=True)
    
    # Assignment
    assigned_by = Column(String(36), nullable=True)
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # SLA
    sla_deadline = Column(DateTime(timezone=True), nullable=True)
    priority_score = Column(Integer, default=0)
    
    # Status
    status = Column(String(20), nullable=False, default="assigned", index=True)
    # assigned, acknowledged, in_progress, completed, rejected, reassigned
    
    # Escalation
    escalated = Column(String(10), default="false")
    escalated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Action
    action_taken = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    meta_data = Column(JSON, default=dict)

    __table_args__ = (
        Index('idx_assignment_member_status', 'team_member_id', 'status'),
        Index('idx_assignment_report', 'report_id'),
        Index('idx_assignment_sla', 'sla_deadline', 'status'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "report_id": self.report_id,
            "team_member_id": self.team_member_id,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "sla_deadline": self.sla_deadline.isoformat() if self.sla_deadline else None,
            "priority_score": self.priority_score,
            "status": self.status,
            "action_taken": self.action_taken,
            "notes": self.notes,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
