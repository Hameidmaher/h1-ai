"""ConversationRepository — DB access for conversations."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy.orm import Session
from sqlalchemy import func as sqlfunc

from db.models.conversation import Conversation


class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, conv_id: str) -> Optional[Conversation]:
        return self.db.query(Conversation).filter(Conversation.id == conv_id).first()

    def get_by_phone(self, phone: str) -> Optional[Conversation]:
        return self.db.query(Conversation).filter(Conversation.contact_phone == phone).first()

    def list_all(self, status: Optional[str] = None, assigned_to: Optional[str] = None,
                 limit: int = 50, offset: int = 0) -> list[Conversation]:
        q = self.db.query(Conversation)
        if status:
            q = q.filter(Conversation.status == status)
        if assigned_to:
            q = q.filter(Conversation.assigned_to == assigned_to)
        q = q.order_by(Conversation.last_message_at.desc().nullslast())
        return q.offset(offset).limit(limit).all()

    def get_or_create(self, phone: str, name: str = "") -> Conversation:
        conv = self.get_by_phone(phone)
        if not conv:
            conv = Conversation(
                id=str(uuid4()),
                contact_phone=phone,
                contact_name=name or phone,
                status="open",
                last_message_at=datetime.utcnow(),
            )
            self.db.add(conv)
            self.db.commit()
            self.db.refresh(conv)
        return conv

    def update_last_message(self, conv_id: str, content: str, direction: str,
                            classification: Optional[str] = None,
                            priority: Optional[str] = None) -> None:
        conv = self.get_by_id(conv_id)
        if not conv:
            return
        conv.last_message_at = datetime.utcnow()
        conv.last_message_preview = content[:200]
        conv.last_message_direction = direction
        conv.total_messages = (conv.total_messages or 0) + 1
        if direction == "inbound":
            conv.unread_count = (conv.unread_count or 0) + 1
        if classification:
            conv.classification = classification
        if priority:
            conv.priority = priority
        self.db.commit()

    def mark_read(self, conv_id: str) -> None:
        conv = self.get_by_id(conv_id)
        if conv:
            conv.unread_count = 0
            self.db.commit()

    def assign(self, conv_id: str, user_id: str, user_name: str) -> bool:
        conv = self.get_by_id(conv_id)
        if not conv:
            return False
        conv.assigned_to = user_id
        conv.assigned_to_name = user_name
        conv.status = "assigned"
        self.db.commit()
        return True

    def update_status(self, conv_id: str, status: str) -> bool:
        conv = self.get_by_id(conv_id)
        if not conv:
            return False
        conv.status = status
        self.db.commit()
        return True

    def stats(self) -> dict:
        total = self.db.query(sqlfunc.count(Conversation.id)).scalar() or 0
        open_count = self.db.query(sqlfunc.count(Conversation.id)).filter(
            Conversation.status == "open").scalar() or 0
        assigned = self.db.query(sqlfunc.count(Conversation.id)).filter(
            Conversation.status == "assigned").scalar() or 0
        unread_total = self.db.query(sqlfunc.sum(Conversation.unread_count)).scalar() or 0
        return {
            "total_conversations": total,
            "open": open_count,
            "assigned": assigned,
            "unread_total": unread_total,
        }
