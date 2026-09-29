"""System routes — /privacy, /terms."""
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["system"])

_BASE_DIR = Path(__file__).parent.parent
_public_static = _BASE_DIR / "public" / "static"


@router.get("/privacy")
async def privacy_policy():
    """Privacy policy page."""
    return FileResponse(str(_public_static / "privacy.html"))


@router.get("/terms")
async def terms_of_service():
    """Terms of service page."""
    return FileResponse(str(_public_static / "terms.html"))
