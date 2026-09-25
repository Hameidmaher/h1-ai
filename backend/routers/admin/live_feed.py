"""Admin Live Feed routes — /v1/admin/live-feed (SSE)."""
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from models.schemas import User
from auth.dependencies import require_admin
from services.live_feed import live_feed

router = APIRouter(prefix="/v1/admin/live-feed", tags=["admin-live-feed"])


@router.get("")
async def live_feed_stream(request: Request):
    """Server-Sent Events stream for real-time messages."""
    async def event_generator():
        async for event in live_feed.subscribe():
            if await request.is_disconnected():
                break
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/stats")
async def live_feed_stats(user: User = Depends(require_admin)):
    """Get live feed statistics."""
    return live_feed.stats()


@router.post("/test")
async def live_feed_test(user: User = Depends(require_admin)):
    """Send a test event to live feed."""
    await live_feed.broadcast({
        "type": "test",
        "message": "🔔 اختبار البث الحي",
        "from": "system",
    })
    return {"success": True}
