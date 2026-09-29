"""
Session Manager — إدارة جلسات المحادثة (FIXED)
"""
from __future__ import annotations
from datetime import datetime, timedelta
from uuid import uuid4
import json
import structlog
from sqlalchemy import text

logger = structlog.get_logger()


class SessionManager:
    """إدارة جلسات الشات بوت."""

    CONTEXT_WINDOW = 10
    SESSION_TIMEOUT_HOURS = 2

    # ─── Get or Create ─────────────────────────────────
    async def get_or_create(
        self,
        channel: str,
        channel_user_id: str,
        pharmacy_id: str | None = None,
        customer_id: str | None = None,
    ) -> dict:
        """احصل على جلسة نشطة أو أنشئ واحدة جديدة."""
        from db import SessionLocal

        session = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(hours=self.SESSION_TIMEOUT_HOURS)

            sql = text("""
                SELECT id, customer_id, pharmacy_id, context, total_messages
                FROM chatbot_sessions
                WHERE channel = :channel
                  AND channel_user_id = :uid
                  AND is_active = true
                  AND updated_at > :cutoff
                ORDER BY updated_at DESC
                LIMIT 1
            """)

            row = session.execute(sql, {
                "channel": channel,
                "uid": channel_user_id,
                "cutoff": cutoff,
            }).first()

            if row:
                return {
                    "id": str(row.id),
                    "customer_id": str(row.customer_id) if row.customer_id else None,
                    "pharmacy_id": str(row.pharmacy_id) if row.pharmacy_id else None,
                    "context": row.context or {},
                    "total_messages": row.total_messages or 0,
                    "is_new": False,
                }

            # أنشئ جلسة جديدة — بدون ::jsonb بعد الـ params
            new_id = str(uuid4())
            session.execute(text("""
                INSERT INTO chatbot_sessions
                    (id, channel, channel_user_id, pharmacy_id, customer_id, context)
                VALUES
                    (:id, :channel, :uid, :ph, :cust, CAST('{}' AS jsonb))
            """), {
                "id": new_id,
                "channel": channel,
                "uid": channel_user_id,
                "ph": pharmacy_id,
                "cust": customer_id,
            })
            session.commit()

            logger.info("session.created", id=new_id, channel=channel)
            return {
                "id": new_id,
                "customer_id": customer_id,
                "pharmacy_id": pharmacy_id,
                "context": {},
                "total_messages": 0,
                "is_new": True,
            }
        finally:
            session.close()

    # ─── Save Message ──────────────────────────────────
    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        intent: str | None = None,
        entities: dict | None = None,
        tool_calls: list | None = None,
        tool_results: list | None = None,
        model: str | None = None,
        tokens_in: int = 0,
        tokens_out: int = 0,
        latency_ms: int = 0,
        is_error: bool = False,
    ) -> int:
        """احفظ رسالة — مع CAST بدل ::jsonb."""
        from db import SessionLocal

        session = SessionLocal()
        try:
            # ✅ CAST بدل :: — الحل الأساسي
            result = session.execute(text("""
                INSERT INTO chatbot_messages
                    (session_id, role, content, intent, entities,
                     tool_calls, tool_results, model, tokens_in, tokens_out,
                     latency_ms, is_error)
                VALUES
                    (:sid, :role, :content, :intent,
                     CAST(:entities AS jsonb),
                     CAST(:tc AS jsonb),
                     CAST(:tr AS jsonb),
                     :model, :ti, :to, :lat, :err)
                RETURNING id
            """), {
                "sid": session_id,
                "role": role,
                "content": content,
                "intent": intent,
                "entities": json.dumps(entities, ensure_ascii=False) if entities else None,
                "tc": json.dumps(tool_calls, ensure_ascii=False) if tool_calls else None,
                "tr": json.dumps(tool_results, ensure_ascii=False) if tool_results else None,
                "model": model,
                "ti": tokens_in,
                "to": tokens_out,
                "lat": latency_ms,
                "err": is_error,
            })

            msg_id = result.scalar()

            # حدّث عداد الجلسة
            session.execute(text("""
                UPDATE chatbot_sessions
                SET total_messages = total_messages + 1,
                    updated_at = now()
                WHERE id = :sid
            """), {"sid": session_id})

            session.commit()
            return msg_id
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    # ─── Get Context ───────────────────────────────────
    async def get_context(self, session_id: str) -> list[dict]:
        """جيب آخر N رسائل للسياق."""
        from db import SessionLocal

        session = SessionLocal()
        try:
            rows = session.execute(text("""
                SELECT role, content
                FROM chatbot_messages
                WHERE session_id = :sid
                  AND role IN ('user', 'assistant')
                ORDER BY created_at DESC
                LIMIT :n
            """), {"sid": session_id, "n": self.CONTEXT_WINDOW}).fetchall()

            return [
                {"role": r.role, "content": r.content}
                for r in reversed(rows)
            ]
        finally:
            session.close()
