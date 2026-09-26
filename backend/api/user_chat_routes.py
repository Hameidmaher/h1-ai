"""Chat API — للمستخدمين المسجلين."""
from __future__ import annotations
import time
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import json, asyncio

from auth.dependencies import get_current_user
from auth.models import User

import structlog
logger = structlog.get_logger()
router = APIRouter(prefix="/v1/user", tags=["user-chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


@router.post("/chat")
async def user_chat(req: ChatRequest, user: User = Depends(get_current_user)):
    """شات عادي (بدون streaming)."""
    try:
        from chatbot.core import get_core
        core = get_core()
        t0 = time.time()
        response = await core.chat(
            message=req.message,
            channel="web",
            channel_user_id=user.id,
            pharmacy_id=getattr(user, "pharmacy_id", None),
        )
        # نسجّل النشاط
        try:
            from api.monitoring_routes import _metrics
            _metrics["chat_activity"].append({
                "ts": time.time(),
                "user": user.username,
                "message": req.message[:100],
                "tools": [t.get("name") for t in (response.tool_calls or [])],
            })
        except Exception:
            pass
        return {
            "reply": response.text,
            "session_id": response.session_id,
            "message_id": response.message_id,
            "tools_used": [t.get("name") for t in (response.tool_calls or [])],
            "latency_ms": int((time.time() - t0) * 1000),
        }
    except Exception as e:
        logger.error("user.chat.failed", error=str(e))
        raise HTTPException(500, f"فشل الشات: {str(e)[:150]}")


@router.post("/chat/stream")
async def user_chat_stream(req: ChatRequest, user: User = Depends(get_current_user)):
    """شات streaming (SSE)."""
    async def gen():
        try:
            from chatbot.core import get_core
            core = get_core()
            yield f"event: start\ndata: {json.dumps({'status': 'thinking'})}\n\n"
            response = await core.chat(
                message=req.message,
                channel="web",
                channel_user_id=user.id,
                pharmacy_id=getattr(user, "pharmacy_id", None),
            )
            if response.tool_calls:
                tools = [{"name": t["name"], "success": t.get("error") is None} for t in response.tool_calls]
                yield f"event: tools\ndata: {json.dumps({'tools': tools})}\n\n"
            words = response.text.split()
            for i, w in enumerate(words):
                chunk = w + (" " if i < len(words) - 1 else "")
                yield f"event: chunk\ndata: {json.dumps({'text': chunk})}\n\n"
                await asyncio.sleep(0.02)
            yield f"event: done\ndata: {json.dumps({'session_id': response.session_id, 'message_id': response.message_id})}\n\n"
            # نسجّل النشاط
            try:
                from api.monitoring_routes import _metrics
                _metrics["chat_activity"].append({
                    "ts": time.time(),
                    "user": user.username,
                    "message": req.message[:100],
                    "tools": [t.get("name") for t in (response.tool_calls or [])],
                })
            except Exception:
                pass
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)[:200]})}\n\n"
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/sessions")
async def user_sessions(user: User = Depends(get_current_user)):
    """قائمة المحادثات السابقة."""
    try:
        from api.monitoring_routes import _metrics
        recent = [
            c for c in list(_metrics["chat_activity"])
            if c.get("user") == user.username
        ][-20:]
        return {"sessions": recent, "total": len(recent)}
    except Exception as e:
        return {"sessions": [], "error": str(e)}
