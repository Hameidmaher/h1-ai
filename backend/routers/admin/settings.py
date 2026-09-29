"""Admin settings routes — /v1/admin/settings/*."""
from fastapi import APIRouter, Depends, HTTPException, Request

from models.schemas import User
from auth.dependencies import require_admin
from services.settings_service import settings_service

router = APIRouter(prefix="/v1/admin/settings", tags=["admin-settings"])


@router.get("")
async def get_settings(user: User = Depends(require_admin)):
    """Get all settings."""
    return {
        "whatsapp": settings_service.get_whatsapp(),
        "app": settings_service.load().get("app", {}),
        "features": settings_service.load().get("features", {}),
    }


@router.get("/whatsapp")
async def get_whatsapp_settings(user: User = Depends(require_admin)):
    """Get WhatsApp settings."""
    return settings_service.get_whatsapp()


@router.put("/whatsapp")
async def update_whatsapp_settings(
    request: Request,
    user: User = Depends(require_admin),
):
    """Update WhatsApp settings."""
    try:
        updates = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    if "phone" in updates:
        phone = str(updates["phone"]).strip()
        if phone and not (phone.startswith("+") or phone.isdigit()):
            raise HTTPException(
                status_code=400,
                detail="Phone must start with + or be digits",
            )
        updates["phone"] = phone

    if "mode" in updates:
        if updates["mode"] not in ("link", "qr", "api"):
            raise HTTPException(
                status_code=400,
                detail="Mode must be link, qr, or api",
            )

    if "enabled" in updates:
        updates["enabled"] = bool(updates["enabled"])

    result = settings_service.update_whatsapp(updates)
    return {"success": True, "whatsapp": result}
