"""Streaming Chat API — SSE"""
import json
import asyncio
from fastapi import APIRouter, Request
from middleware.rate_limit import limiter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import structlog

from chatbot.core import get_core

logger = structlog.get_logger()
router = APIRouter(prefix="/api/chat", tags=["chat-stream"])


class StreamRequest(BaseModel):
    message: str
    channel: str = "web"
    channel_user_id: str
    pharmacy_id: Optional[str] = None
    customer_id: Optional[str] = None


@router.post("/stream")
@limiter.limit("20/minute")
async def chat_stream(request: Request, req: StreamRequest):
    """Streaming response — يُرسل الردود تدريجياً."""

    async def event_generator():
        try:
            core = get_core()
            yield f"event: start\ndata: {json.dumps({'status': 'thinking'})}\n\n"

            response = await core.chat(
                message=req.message,
                channel=req.channel,
                channel_user_id=req.channel_user_id,
                pharmacy_id=req.pharmacy_id,
                customer_id=req.customer_id,
            )

            if response.tool_calls:
                tools = [
                    {"name": t["name"], "success": t.get("error") is None}
                    for t in response.tool_calls
                ]
                yield f"event: tools\ndata: {json.dumps({'tools': tools})}\n\n"

            words = response.text.split()
            for i, word in enumerate(words):
                chunk = word + (" " if i < len(words) - 1 else "")
                yield f"event: chunk\ndata: {json.dumps({'text': chunk})}\n\n"
                await asyncio.sleep(0.03)

            yield f"event: done\ndata: {json.dumps({
                'session_id': response.session_id,
                'message_id': response.message_id,
                'tools_used': [t['name'] for t in response.tool_calls],
                'latency_ms': response.latency_ms,
            })}\n\n"

        except Exception as e:
            logger.error("stream.failed", error=str(e)[:200])
            yield f"event: error\ndata: {json.dumps({'error': str(e)[:100]})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )

# Force rebuild for FastAPI OpenAPI (fix: PydanticUserError on ForwardRef)
StreamRequest.model_rebuild()
