"""Chat History — حفظ واسترجاع المحادثات (chat_sessions + chat_history)."""
from __future__ import annotations
from typing import Optional
from datetime import datetime
import uuid
import json
import structlog

logger = structlog.get_logger()


def create_session(
    user_id: str,
    role: str,
    pharmacy_id: str = None,
    channel: str = "web",
    title: str = None,
) -> Optional[str]:
    """ينشئ session جديدة ويرجّع ID."""
    from db import SessionLocal
    from sqlalchemy import text

    db = SessionLocal()
    try:
        session_id = str(uuid.uuid4())
        db.execute(
            text("""
                INSERT INTO chat_sessions (id, user_id, pharmacy_id, role, channel, title)
                VALUES (:id, :uid, :pid, :role, :ch, :title)
            """),
            {
                "id": session_id,
                "uid": user_id,
                "pid": pharmacy_id,
                "role": role,
                "ch": channel,
                "title": title or f"محادثة {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            }
        )
        db.commit()
        return session_id
    except Exception as e:
        logger.error("session.create.failed", error=str(e)[:200])
        db.rollback()
        return None
    finally:
        db.close()


def get_or_create_session(
    user_id: str,
    role: str,
    pharmacy_id: str = None,
    channel: str = "web",
    session_id: str = None,
) -> Optional[str]:
    """يرجّع session موجودة أو ينشئ جديدة."""
    from db import SessionLocal
    from sqlalchemy import text

    if session_id:
        return session_id

    db = SessionLocal()
    try:
        row = db.execute(
            text("""
                SELECT id FROM chat_sessions
                WHERE user_id = :uid AND role = :role AND channel = :ch AND is_active = true
                ORDER BY updated_at DESC
                LIMIT 1
            """),
            {"uid": user_id, "role": role, "ch": channel}
        ).fetchone()

        if row:
            return str(row.id)
    except Exception:
        pass
    finally:
        db.close()

    return create_session(user_id, role, pharmacy_id, channel)


def save_message(
    session_id: str,
    sender: str,
    content: str,
    tools_used: list = None,
    metadata: dict = None,
) -> Optional[str]:
    """يحفظ رسالة في الـ DB."""
    if not session_id:
        return None

    from db import SessionLocal
    from sqlalchemy import text

    db = SessionLocal()
    try:
        msg_id = str(uuid.uuid4())
        db.execute(
            text("""
                INSERT INTO chat_history 
                    (id, session_id, sender, content, tools_used, metadata)
                VALUES 
                    (:id, :sid, :sender, :content, :tools::jsonb, :meta::jsonb)
            """),
            {
                "id": msg_id,
                "sid": session_id,
                "sender": sender,
                "content": content,
                "tools": json.dumps(tools_used or []),
                "meta": json.dumps(metadata or {}),
            }
        )
        db.commit()

        # تحديث updated_at
        db.execute(
            text("UPDATE chat_sessions SET updated_at = NOW() WHERE id = :sid"),
            {"sid": session_id}
        )
        db.commit()

        return msg_id
    except Exception as e:
        logger.error("message.save.failed", error=str(e)[:200])
        db.rollback()
        return None
    finally:
        db.close()


def get_session_messages(session_id: str, limit: int = 50) -> list:
    """يرجّع رسائل session."""
    from db import SessionLocal
    from sqlalchemy import text

    db = SessionLocal()
    try:
        rows = db.execute(
            text("""
                SELECT id, sender, content, tools_used, metadata, rating, created_at
                FROM chat_history
                WHERE session_id = :sid
                ORDER BY created_at ASC
                LIMIT :lim
            """),
            {"sid": session_id, "lim": limit}
        ).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception as e:
        logger.error("messages.get.failed", error=str(e)[:200])
        return []
    finally:
        db.close()


def list_sessions(user_id: str, role: str = None, limit: int = 20) -> list:
    """يرجّع sessions المستخدم."""
    from db import SessionLocal
    from sqlalchemy import text

    db = SessionLocal()
    try:
        if role:
            rows = db.execute(
                text("""
                    SELECT id, role, channel, title, created_at, updated_at,
                           (SELECT COUNT(*) FROM chat_history WHERE session_id = chat_sessions.id) as message_count
                    FROM chat_sessions
                    WHERE user_id = :uid AND role = :role
                    ORDER BY updated_at DESC
                    LIMIT :lim
                """),
                {"uid": user_id, "role": role, "lim": limit}
            ).fetchall()
        else:
            rows = db.execute(
                text("""
                    SELECT id, role, channel, title, created_at, updated_at,
                           (SELECT COUNT(*) FROM chat_history WHERE session_id = chat_sessions.id) as message_count
                    FROM chat_sessions
                    WHERE user_id = :uid
                    ORDER BY updated_at DESC
                    LIMIT :lim
                """),
                {"uid": user_id, "lim": limit}
            ).fetchall()
        return [dict(r._mapping) for r in rows]
    except Exception as e:
        logger.error("sessions.list.failed", error=str(e)[:200])
        return []
    finally:
        db.close()


def rate_message(message_id: str, rating: str) -> bool:
    """تقييم رسالة."""
    from db import SessionLocal
    from sqlalchemy import text

    db = SessionLocal()
    try:
        db.execute(
            text("UPDATE chat_history SET rating = :r WHERE id = :id"),
            {"r": rating, "id": message_id}
        )
        db.commit()
        return True
    except Exception as e:
        logger.error("message.rate.failed", error=str(e)[:200])
        return False
    finally:
        db.close()
