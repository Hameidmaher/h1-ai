"""Admin Chat — شات بوت للمدير العام."""
from __future__ import annotations
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth.dependencies import require_super_admin
from auth.models import User
from db import SessionLocal

import structlog
logger = structlog.get_logger()
router = APIRouter(prefix="/v1/admin/chat", tags=["admin-chat"])


class AdminChatRequest(BaseModel):
    message: str
    context: Optional[dict] = None


class AdminChatResponse(BaseModel):
    reply: str
    data: Optional[dict] = None
    tools_used: list = []


# ═══ الأدوات الإدارية ═══

async def tool_get_stats():
    db = SessionLocal()
    try:
        from sqlalchemy import text
        stats = {}
        for table in ["users", "pharmacies", "products", "drugs"]:
            try:
                stats[table] = db.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0
            except Exception:
                stats[table] = 0
        return {
            "type": "stats", "data": stats,
            "reply": f"📊 **إحصائيات المنصة**\n\n"
                     f"👥 المستخدمون: {stats.get('users', 0)}\n"
                     f"🏪 الصيدليات: {stats.get('pharmacies', 0)}\n"
                     f"📦 المنتجات: {stats.get('products', 0)}\n"
                     f"💊 الأدوية: {stats.get('drugs', 0)}"
        }
    finally:
        db.close()


async def tool_list_pharmacies():
    db = SessionLocal()
    try:
        from sqlalchemy import text
        rows = db.execute(text("SELECT name, phone, is_active FROM pharmacies ORDER BY name LIMIT 20")).fetchall()
        if not rows:
            return {"reply": "لا توجد صيدليات مسجلة", "type": "pharmacies"}
        reply = f"🏪 **الصيدليات ({len(rows)}):**\n\n"
        for r in rows:
            status = "🟢" if r[2] else "🔴"
            reply += f"{status} {r[0]} — {r[1] or 'لا يوجد رقم'}\n"
        return {"reply": reply, "type": "pharmacies", "data": {"count": len(rows)}}
    finally:
        db.close()


async def tool_list_users():
    db = SessionLocal()
    try:
        from sqlalchemy import text
        rows = db.execute(text("SELECT username, email, role FROM users ORDER BY created_at DESC LIMIT 20")).fetchall()
        if not rows:
            return {"reply": "لا يوجد مستخدمون", "type": "users"}
        reply = f"👥 **المستخدمون ({len(rows)}):**\n\n"
        for r in rows:
            reply += f"• {r[0]} — {r[1] or 'بدون بريد'} ({r[2]})\n"
        return {"reply": reply, "type": "users", "data": {"count": len(rows)}}
    finally:
        db.close()


# ═══ Router ═══

@router.post("/send", response_model=AdminChatResponse)
async def admin_chat_send(
    req: AdminChatRequest,
    user: User = Depends(require_super_admin),
):
    """Chat مع Admin Assistant."""
    msg = req.message.strip()
    if not msg:
        raise HTTPException(400, "الرسالة فارغة")

    logger.info("admin_chat.message", user=user.username, message=msg[:100])

    # 1. الأدوات التقنية
    try:
        from chatbot.roles.admin_tools_enhanced import detect_tech_tool, execute_tech
        tech_tool = detect_tech_tool(msg)
        if tech_tool:
            result = await execute_tech(tech_tool, msg, req.context or {})
            return AdminChatResponse(
                reply=result.get("reply", "..."),
                data=result.get("data"),
                tools_used=result.get("tools_used", [])
            )
    except Exception as e:
        logger.error("admin_chat.tech_error", error=str(e))

    # 2. الأدوات الإدارية
    try:
        from chatbot.roles.admin_tools import detect_tool, execute
        tool = detect_tool(msg)
        if tool:
            result = await execute(tool, req.context or {})
            return AdminChatResponse(
                reply=result.get("reply", "..."),
                data=result.get("data"),
                tools_used=result.get("tools_used", [])
            )
    except Exception as e:
        logger.error("admin_chat.admin_error", error=str(e))

    # 3. LLM للأسئلة العامة
    try:
        from llm.groq_client import groq_client
        system_prompt = """أنت "مساعد الإدارة" لـ H1-AI.

معرفة:
- Backend: FastAPI + Python 3.13
- DB: PostgreSQL 17 + Redis 8
- LLM: Groq (llama-3.3-70b)
- Agents: LangChain + LangGraph
- WhatsApp: Baileys (Node.js)

أجب بالعربية. موجز ومفيد."""

        response = await groq_client.chat(system=system_prompt, user=msg, max_tokens=500)
        return AdminChatResponse(reply=response, tools_used=["llm"])
    except Exception as e:
        logger.error("admin_chat.llm_error", error=str(e))
        return AdminChatResponse(
            reply="❌ جرب:\n• 'حالة الخدمات'\n• 'إحصائيات'\n• 'اشرح orchestrator'\n• 'بماذا مبني المشروع'",
            tools_used=[]
        )


@router.get("/help")
async def admin_chat_help():
    return {
        "capabilities": {
            "stats": ["إحصائيات", "كم عدد"],
            "pharmacies": ["الصيدليات"],
            "users": ["المستخدمين"],
            "services_status": ["حالة الخدمات"],
            "system_health": ["صحة النظام", "CPU"],
            "recent_errors": ["الأخطاء"],
            "tech_stack": ["بماذا مبني"],
            "architecture": ["البنية"],
            "project_structure": ["بنية المشروع"],
            "explain_code": ["اشرح orchestrator"],
        }
    }
