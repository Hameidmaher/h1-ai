"""Analytics API — إحصائيات للـ dashboard."""
from fastapi import APIRouter
from datetime import datetime, timedelta
from sqlalchemy import text
from typing import Optional

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview")
async def overview():
    """نظرة عامة."""
    from db import SessionLocal
    s = SessionLocal()
    try:
        r = s.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM chatbot_sessions) AS total_sessions,
                (SELECT COUNT(*) FROM chatbot_messages) AS total_messages,
                (SELECT COUNT(*) FROM chatbots_sessions WHERE created_at > now() - interval '24 hours') AS sessions_24h,
                (SELECT COUNT(*) FROM chatbot_messages WHERE created_at > now() - interval '24 hours') AS messages_24h,
                (SELECT COUNT(*) FROM drugs) AS total_drugs,
                (SELECT COUNT(*) FROM customers) AS total_customers,
                (SELECT COUNT(*) FROM orders) AS total_orders
        """)).first()

        return {
            "total_sessions": r[0] or 0,
            "total_messages": r[1] or 0,
            "sessions_24h": r[2] or 0,
            "messages_24h": r[3] or 0,
            "total_drugs": r[4] or 0,
            "total_customers": r[5] or 0,
            "total_orders": r[6] or 0,
        }
    finally:
        s.close()


@router.get("/messages/timeseries")
async def messages_timeseries(days: int = 7):
    """عدد الرسائل يوميًا."""
    from db import SessionLocal
    s = SessionLocal()
    try:
        rows = s.execute(text("""
            SELECT
                DATE_TRUNC('day', created_at)::date AS day,
                COUNT(*) AS count
            FROM chatbot_messages
            WHERE created_at > now() - make_interval(days => :d)
            GROUP BY day
            ORDER BY day
        """), {"d": days}).fetchall()

        return [{"date": str(r[0]), "count": r[1]} for r in rows]
    finally:
        s.close()


@router.get("/intents/top")
async def top_intents(limit: int = 10):
    """أكثر الأدوات استخدامًا."""
    from db import SessionLocal
    s = SessionLocal()
    try:
        rows = s.execute(text("""
            SELECT
                tool_name,
                COUNT(*) AS count
            FROM (
                SELECT jsonb_array_elements(tool_calls)->>'name' AS tool_name
                FROM chatbot_messages
                WHERE tool_calls IS NOT NULL
                  AND jsonb_typeof(tool_calls) = 'array'
            ) t
            WHERE tool_name IS NOT NULL
            GROUP BY tool_name
            ORDER BY count DESC
            LIMIT :n
        """), {"n": limit}).fetchall()

        return [{"tool": r[0], "count": r[1]} for r in rows]
    finally:
        s.close()


@router.get("/sessions/recent")
async def recent_sessions(limit: int = 10):
    """آخر الجلسات."""
    from db import SessionLocal
    s = SessionLocal()
    try:
        rows = s.execute(text("""
            SELECT
                id, channel, channel_user_id,
                total_messages, created_at
            FROM chatbot_sessions
            ORDER BY created_at DESC
            LIMIT :n
        """), {"n": limit}).fetchall()

        return [{
            "id": str(r[0]),
            "channel": r[1],
            "user": r[2][:15] + "..." if len(r[2]) > 15 else r[2],
            "messages": r[3] or 0,
            "created_at": r[4].isoformat(),
        } for r in rows]
    finally:
        s.close()
