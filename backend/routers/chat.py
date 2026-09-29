"""Chat routes — /v1/chat, /v1/chat/stream."""
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from config import settings
from models.schemas import ChatRequest, ChatResponse, User
from core.orchestrator import orchestrator
from middleware.rate_limit import limiter
from services.chat_cache import chat_cache
from session.session_store import session_store
from auth.dependencies import get_current_user
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/v1/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
@limiter.limit(settings.rate_limit_chat)
async def chat(
    request: Request,
    req: ChatRequest,
    user: User = Depends(get_current_user),
):
    session_id = req.session_id or str(uuid4())

    # ═══ Check cache first ═══
    cached = chat_cache.get(req.message, user.role)
    if cached:
        session = session_store.get(session_id) or {"user_id": user.id, "messages": []}
        session["messages"].append({"role": "user", "content": req.message})
        session["messages"].append({"role": "agent", "content": cached["data"]["text"]})
        session_store.set(session_id, session)
        return ChatResponse(
            data=cached["data"],
            user_type=cached["user_type"],
            session_id=session_id,
            route_method="cache",
            handler=cached["handler"],
        )

    try:
        import asyncio
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: orchestrator.handle(req.message, user_role=user.role),
        )
        session = session_store.get(session_id) or {"user_id": user.id, "messages": []}
        session["messages"].append({"role": "user", "content": req.message})
        session["messages"].append({"role": "agent", "content": result.response.text})
        session_store.set(session_id, session)
        return ChatResponse(
            data=result.response,
            user_type=result.user_type,
            session_id=session_id,
            route_method=result.route_method,
            handler=result.handler,
        )
    except Exception as e:
        logger.error("chat.error", error=str(e), user=user.id)
        raise HTTPException(status_code=500, detail="حدث خطأ داخلي")


@router.post("/stream")
@limiter.limit(settings.rate_limit_chat)
async def chat_stream(
    request: Request,
    req: ChatRequest,
    user: User = Depends(get_current_user),
):
    """Streaming chat endpoint using Server-Sent Events (SSE)."""
    import json
    import asyncio

    async def event_generator():
        session_id = req.session_id or str(uuid4())
        yield f"data: {json.dumps({'type': 'start', 'session_id': session_id})}\n\n"

        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: orchestrator.handle(req.message, user_role=user.role),
            )
            text = result.response.text or ""

            chunk_size = 2
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i+chunk_size]
                yield f"data: {json.dumps({'type': 'chunk', 'text': chunk}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.015)

            session = session_store.get(session_id) or {"user_id": user.id, "messages": []}
            session["messages"].append({"role": "user", "content": req.message})
            session["messages"].append({"role": "agent", "content": text})
            session_store.set(session_id, session)

            done_data = {
                'type': 'done',
                'session_id': session_id,
                'handler': result.handler,
                'confidence': result.response.confidence,
                'needs_human': result.response.needs_human,
                'action': result.response.action,
                'products_referenced': result.response.products_referenced or [],
            }
            yield f"data: {json.dumps(done_data, ensure_ascii=False)}\n\n"

        except Exception as e:
            logger.error("chat_stream.error", error=str(e), user=user.id)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
