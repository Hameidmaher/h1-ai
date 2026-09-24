"""Message — WhatsApp message received/sent."""
from sqlalchemy import Column, String, Boolean, Text, DateTime, JSON, Index
from sqlalchemy.sql import func
from db.base import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True)
    whatsapp_id = Column(String(100), unique=True, nullable=True, index=True)
    
    # Sender
    from_phone = Column(String(20), nullable=False, index=True)
    from_name = Column(String(100), nullable=True)
    to_phone = Column(String(20), nullable=True)
    
    # Content
    content = Column(Text, nullable=False)
    media_url = Column(String(500), nullable=True)
    media_type = Column(String(30), nullable=True)  # text, image, audio, document
    
    # Classification
    direction = Column(String(10), nullable=False, default="inbound")  # inbound/outbound
    classification = Column(String(30), nullable=True, index=True)
    # customer, supplier, spam, urgent, unknown
    priority = Column(String(20), default="normal", index=True)
    # low, normal, high, urgent
    
    # Processing
    processed = Column(Boolean, default=False, nullable=False, index=True)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    chatbot_response = Column(Text, nullable=True)
    handler = Column(String(50), nullable=True)  # chatbot/advisory/agent/human
    
    # Metadata
    meta_data = Column(JSON, default=dict)
    
    # Timestamps
    received_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_message_from_date', 'from_phone', 'received_at'),
        Index('idx_message_class_priority', 'classification', 'priority'),
        Index('idx_message_processed', 'processed', 'received_at'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "whatsapp_id": self.whatsapp_id,
            "from_phone": self.from_phone,
            "from_name": self.from_name,
            "to_phone": self.to_phone,
            "content": self.content,
            "media_type": self.media_type,
            "direction": self.direction,
            "classification": self.classification,
            "priority": self.priority,
            "processed": self.processed,
            "chatbot_response": self.chatbot_response,
            "handler": self.handler,
            "received_at": self.received_at.isoformat() if self.received_at else None,
        }
