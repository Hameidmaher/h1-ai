"""Message Repository."""
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from db.models.message import Message


class MessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs) -> Message:
        msg = Message(**kwargs)
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_by_id(self, msg_id: str) -> Optional[Message]:
        return self.db.query(Message).filter(Message.id == msg_id).first()

    def get_by_whatsapp_id(self, wa_id: str) -> Optional[Message]:
        return self.db.query(Message).filter(Message.whatsapp_id == wa_id).first()

    def list_recent(
        self,
        limit: int = 100,
        classification: Optional[str] = None,
        priority: Optional[str] = None,
        from_phone: Optional[str] = None,
        processed: Optional[bool] = None,
    ) -> list[Message]:
        q = self.db.query(Message).order_by(Message.received_at.desc())
        if classification:
            q = q.filter(Message.classification == classification)
        if priority:
            q = q.filter(Message.priority == priority)
        if from_phone:
            q = q.filter(Message.from_phone == from_phone)
        if processed is not None:
            q = q.filter(Message.processed == processed)
        return q.limit(limit).all()

    def list_unprocessed(self, limit: int = 50) -> list[Message]:
        return self.db.query(Message).filter(
            not Message.processed,
            Message.direction == "inbound",
        ).order_by(Message.received_at.asc()).limit(limit).all()

    def mark_processed(self, msg_id: str, response: str = None, handler: str = None):
        msg = self.get_by_id(msg_id)
        if not msg:
            return None
        msg.processed = True
        msg.processed_at = datetime.utcnow()
        if response:
            msg.chatbot_response = response
        if handler:
            msg.handler = handler
        self.db.commit()
        return msg

    def count(self, **filters) -> int:
        q = self.db.query(Message)
        for key, value in filters.items():
            if hasattr(Message, key):
                q = q.filter(getattr(Message, key) == value)
        return q.count()

    def stats(self, since_hours: int = 24) -> dict:
        since = datetime.utcnow() - timedelta(hours=since_hours)
        q = self.db.query(Message).filter(Message.received_at >= since)
        
        total = q.count()
        inbound = q.filter(Message.direction == "inbound").count()
        outbound = q.filter(Message.direction == "outbound").count()
        
        # By classification
        from sqlalchemy import func
        by_class = dict(
            self.db.query(Message.classification, func.count(Message.id))
            .filter(Message.received_at >= since)
            .group_by(Message.classification)
            .all()
        )
        
        return {
            "period_hours": since_hours,
            "total": total,
            "inbound": inbound,
            "outbound": outbound,
            "by_classification": by_class,
        }
