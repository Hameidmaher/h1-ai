"""Cache routes — /v1/cache/stats, /v1/cache/clear, /v1/cache/save."""
from fastapi import APIRouter, Depends

from models.schemas import User
from auth.dependencies import require_admin
from services.chat_cache import chat_cache

router = APIRouter(prefix="/v1/cache", tags=["cache"])


@router.get("/stats")
async def cache_stats(user: User = Depends(require_admin)):
    """Get chat cache statistics."""
    return chat_cache.stats()


@router.post("/clear")
async def cache_clear(user: User = Depends(require_admin)):
    """Clear chat cache."""
    chat_cache.clear()
    return {"success": True, "message": "Cache cleared"}


@router.post("/save")
async def cache_save(user: User = Depends(require_admin)):
    """Save cache to disk."""
    chat_cache.save_to_disk()
    return {"success": True}
