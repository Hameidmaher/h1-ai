"""Report — structured report generated from a message."""
from sqlalchemy import Column, String, Text, DateTime, JSON, Index, ForeignKey
from sqlalchemy.sql import func
from db.base import Base


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True)
    message_id = Column(String(36), ForeignKey("messages.id"), nullable=False, index=True)
    
    # Classification
    type = Column(String(50), nullable=False, index=True)
    # customer_inquiry, supplier_offer, complaint, urgent, prescription, etc.
    category = Column(String(50), nullable=True, index=True)
    # product_inquiry, drug_info, interaction_check, prescription_review, etc.
    priority = Column(String(20), nullable=False, default="normal", index=True)
    
    # Content
    title = Column(String(200), nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(JSON, nullable=False)  # structured content
    
    # Assignment
    assigned_to = Column(String(36), ForeignKey("team_members.id"), nullable=True, index=True)
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(String(20), nullable=False, default="pending", index=True)
    # pending, assigned, in_progress, resolved, escalated, cancelled
    
    # SLA
    sla_deadline = Column(DateTime(timezone=True), nullable=True)
    escalated_at = Column(DateTime(timezone=True), nullable=True)
    escalation_reason = Column(String(200), nullable=True)
    
    # Resolution
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_by = Column(String(36), nullable=True)
    
    # Metrics
    response_time_seconds = Column(String(20), nullable=True)
    resolution_time_seconds = Column(String(20), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index('idx_report_status_priority', 'status', 'priority'),
        Index('idx_report_assigned_status', 'assigned_to', 'status'),
        Index('idx_report_type_status', 'type', 'status'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "message_id": self.message_id,
            "type": self.type,
            "category": self.category,
            "priority": self.priority,
            "title": self.title,
            "summary": self.summary,
            "content": self.content,
            "assigned_to": self.assigned_to,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else None,
            "status": self.status,
            "sla_deadline": self.sla_deadline.isoformat() if self.sla_deadline else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_notes": self.resolution_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
