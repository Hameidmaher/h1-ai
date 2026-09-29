"""Chat Streaming — SSE for all roles."""
from __future__ import annotations
import json
import asyncio
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from auth.dependencies import get_current_user, require_super_admin, require_pharmacist
from auth.models import User
from chatbot.roles.orchestrator import route_message

import structlog
logger = structlog.get_logger()
router = APIRouter(prefix="/v1/chat/stream", tags=["chat-stream-v2"])


class StreamRequest(BaseModel):
    message: str
    context: dict = {}


def _format_sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/admin")
async def stream_admin(req: StreamRequest, user: User = Depends(require_super_admin)):
    return await _stream_response("admin", req.message, {"user_id": user.id})


@router.post("/pharmacy")
async def stream_pharmacy(req: StreamRequest, user: User = Depends(require_pharmacist)):
    return await _stream_response(
        "pharmacy", req.message,
        {"user_id": user.id, "pharmacy_id": getattr(user, "pharmacy_id", None)}
    )


@router.post("/customer")
async def stream_customer(req: StreamRequest, user: User = Depends(get_current_user)):
    return await _stream_response("customer", req.message, {"user_id": user.id})


async def _stream_response(role: str, message: str, context: dict):
    async def gen():
        try:
            yield _format_sse("start", {"status": "thinking"})

            result = await route_message(role=role, message=message, context=context)

            tools = result.get("tools_used", [])
            if tools:
                yield _format_sse("tools", {"tools": tools})

            reply = result.get("reply", "")
            words = reply.split()
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield _format_sse("chunk", {"text": chunk})
                await asyncio.sleep(0.02)

            yield _format_sse("done", {
                "total_words": len(words),
                "tools_used": tools,
            })
        except Exception as e:
            logger.error("stream.failed", role=role, error=str(e))
            yield _format_sse("error", {"error": str(e)[:200]})

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
