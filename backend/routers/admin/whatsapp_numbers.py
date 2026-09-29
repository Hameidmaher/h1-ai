"""Admin WhatsApp numbers routes — /v1/admin/whatsapp*."""
from fastapi import APIRouter, Depends, HTTPException, Request

from models.schemas import User
from auth.dependencies import require_admin
from services.pharmacy_service import pharmacy_service

router = APIRouter(prefix="/v1/admin", tags=["admin-whatsapp-numbers"])


# ═══════════════════════════════════════════════════════════
#  WHATSAPP NUMBERS CRUD (5)
# ═══════════════════════════════════════════════════════════
@router.get("/whatsapp")
async def list_all_whatsapp(user: User = Depends(require_admin)):
    """List all WhatsApp numbers."""
    return {"numbers": pharmacy_service.list_whatsapp_numbers()}


@router.get("/pharmacies/{pharmacy_id}/whatsapp")
async def list_pharmacy_whatsapp(pharmacy_id: str, user: User = Depends(require_admin)):
    """List WhatsApp numbers for one pharmacy."""
    return {"numbers": pharmacy_service.list_whatsapp_numbers(pharmacy_id)}


@router.post("/pharmacies/{pharmacy_id}/whatsapp")
async def add_whatsapp(pharmacy_id: str, request: Request, user: User = Depends(require_admin)):
    """Add a WhatsApp number to pharmacy."""
    data = await request.json()
    if not data.get("phone_number"):
        raise HTTPException(status_code=400, detail="Phone required")
    return pharmacy_service.add_whatsapp_number(pharmacy_id, data)


@router.put("/whatsapp/{number_id}")
async def update_whatsapp(number_id: str, request: Request, user: User = Depends(require_admin)):
    """Update WhatsApp number."""
    data = await request.json()
    result = pharmacy_service.update_whatsapp_number(number_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Number not found")
    return result


@router.delete("/whatsapp/{number_id}")
async def delete_whatsapp(number_id: str, user: User = Depends(require_admin)):
    """Delete WhatsApp number."""
    pharmacy_service.delete_whatsapp_number(number_id)
    return {"success": True}
