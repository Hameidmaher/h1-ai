"""Inbox Service — manage conversations + messages."""
from __future__ import annotations
from typing import Optional
from uuid import uuid4

import structlog
from sqlalchemy import text

from db import SessionLocal
from db.repositories.conversation_repo import ConversationRepository
from services.live_feed import live_feed

logger = structlog.get_logger()


class InboxService:
    def get_conversations(self, status: Optional[str] = None, assigned_to: Optional[str] = None,
                          limit: int = 50, offset: int = 0) -> list[dict]:
        db = SessionLocal()
        try:
            repo = ConversationRepository(db)
            convs = repo.list_all(status=status, assigned_to=assigned_to, limit=limit, offset=offset)
            return [c.to_dict() for c in convs]
        finally:
            db.close()

    def get_conversation(self, conv_id: str) -> Optional[dict]:
        db = SessionLocal()
        try:
            repo = ConversationRepository(db)
            conv = repo.get_by_id(conv_id)
            if not conv:
                return None
            result = db.execute(text("""
                SELECT id, from_phone, from_name, content, media_type, media_url,
                       direction, classification, priority, handler, received_at
                FROM messages
                WHERE from_phone = :phone OR to_phone = :phone
                ORDER BY received_at ASC
                LIMIT 200
            """), {"phone": conv.contact_phone})
            messages = [dict(r._mapping) for r in result]
            data = conv.to_dict()
            data["messages"] = messages
            return data
        finally:
            db.close()

    async def reply(self, conv_id: str, content: str, sender_id: str, sender_name: str) -> dict:
        db = SessionLocal()
        try:
            repo = ConversationRepository(db)
            conv = repo.get_by_id(conv_id)
            if not conv:
                raise ValueError("conversation not found")

            msg_id = str(uuid4())
            db.execute(text("""
                INSERT INTO messages (id, from_phone, to_phone, content,
                    direction, media_type, handler, processed)
                VALUES (:id, :from_phone, :to_phone, :content,
                    'outbound', 'text', 'human', TRUE)
            """), {
                "id": msg_id,
                "from_phone": "system",
                "to_phone": conv.contact_phone,
                "content": content,
            })
            db.commit()

            repo.update_last_message(conv.id, content, "outbound")
            repo.mark_read(conv.id)

            await live_feed.broadcast({
                "type": "message_replied",
                "conversation_id": conv.id,
                "message_id": msg_id,
                "contact_phone": conv.contact_phone,
                "content": content[:100],
                "sender": sender_name,
            })

            return {"success": True, "message_id": msg_id}
        finally:
            db.close()

    async def assign(self, conv_id: str, user_id: str, user_name: str) -> dict:
        db = SessionLocal()
        try:
            repo = ConversationRepository(db)
            ok = repo.assign(conv_id, user_id, user_name)
            if ok:
                await live_feed.broadcast({
                    "type": "conversation_assigned",
                    "conversation_id": conv_id,
                    "assigned_to": user_name,
                })
            return {"success": ok}
        finally:
            db.close()

    async def update_status(self, conv_id: str, status: str) -> dict:
        db = SessionLocal()
        try:
            repo = ConversationRepository(db)
            ok = repo.update_status(conv_id, status)
            if ok:
                await live_feed.broadcast({
                    "type": "conversation_status_changed",
                    "conversation_id": conv_id,
                    "status": status,
                })
            return {"success": ok}
        finally:
            db.close()

    def stats(self) -> dict:
        db = SessionLocal()
        try:
            repo = ConversationRepository(db)
            return repo.stats()
        finally:
            db.close()


inbox_service = InboxService()
