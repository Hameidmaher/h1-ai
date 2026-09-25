"""Conversation — grouping of messages by contact."""
from sqlalchemy import Column, String, Integer, DateTime, JSON, Index, Text
from sqlalchemy.sql import func
from db.base import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True)
    contact_phone = Column(String(20), nullable=False, unique=True, index=True)
    contact_name = Column(String(100), nullable=True)

    last_message_at = Column(DateTime(timezone=True), nullable=True, index=True)
    last_message_preview = Column(String(200), nullable=True)
    last_message_direction = Column(String(10), nullable=True)

    status = Column(String(20), default="open", index=True)
    assigned_to = Column(String(36), nullable=True, index=True)
    assigned_to_name = Column(String(100), nullable=True)

    unread_count = Column(Integer, default=0, nullable=False)
    total_messages = Column(Integer, default=0, nullable=False)

    classification = Column(String(30), nullable=True)
    priority = Column(String(20), default="normal", index=True)

    tags = Column(JSON, default=list)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_conv_status_lastmsg', 'status', 'last_message_at'),
        Index('idx_conv_assigned_status', 'assigned_to', 'status'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "contact_phone": self.contact_phone,
            "contact_name": self.contact_name,
            "last_message_at": self.last_message_at.isoformat() if self.last_message_at else None,
            "last_message_preview": self.last_message_preview,
            "last_message_direction": self.last_message_direction,
            "status": self.status,
            "assigned_to": self.assigned_to,
            "assigned_to_name": self.assigned_to_name,
            "unread_count": self.unread_count,
            "total_messages": self.total_messages,
            "classification": self.classification,
            "priority": self.priority,
            "tags": self.tags or [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
