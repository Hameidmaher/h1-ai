"""Multi-Role Chat API — Admin + Pharmacy + Customer."""
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth.dependencies import get_current_user, require_super_admin, require_pharmacist
from auth.models import User
from chatbot.roles.orchestrator import route_message, RoleContext

import structlog
logger = structlog.get_logger()
router = APIRouter(prefix="/v1/chat", tags=["multi-role-chat"])


class ChatRequest(BaseModel):
    message: str
    context: Optional[dict] = None


class ChatResponse(BaseModel):
    reply: str
    tools_used: list = []
    data: Optional[dict] = None


# ═══ Admin ═══
@router.post("/admin/send", response_model=ChatResponse)
async def admin_chat(req: ChatRequest, user: User = Depends(require_super_admin)):
    """شات Super Admin."""
    logger.info("chat.admin", user=user.username, msg=req.message[:80])
    result = await route_message(
        role="admin",
        message=req.message,
        context={"user_id": user.id, **(req.context or {})},
    )
    return ChatResponse(**result)


# ═══ Pharmacy ═══
@router.post("/pharmacy/send", response_model=ChatResponse)
async def pharmacy_chat(req: ChatRequest, user: User = Depends(require_pharmacist)):
    """شات الصيدلي."""
    logger.info("chat.pharmacy", user=user.username, msg=req.message[:80])
    result = await route_message(
        role="pharmacy",
        message=req.message,
        context={
            "user_id": user.id,
            "pharmacy_id": getattr(user, "pharmacy_id", None),
            "phone": getattr(user, "phone", None),
            **(req.context or {}),
        },
    )
    return ChatResponse(**result)


# ═══ Customer ═══
@router.post("/customer/send", response_model=ChatResponse)
async def customer_chat(req: ChatRequest, user: User = Depends(get_current_user)):
    """شات العميل."""
    logger.info("chat.customer", user=user.username, msg=req.message[:80])
    result = await route_message(
        role="customer",
        message=req.message,
        context={"user_id": user.id, **(req.context or {})},
    )
    return ChatResponse(**result)


@router.get("/help/{role}")
async def chat_help(role: str, user: User = Depends(get_current_user)):
    """أمثلة حسب الدور."""
    examples = {
        "admin": ["إحصائيات المنصة", "قائمة الصيدليات", "حالة الخدمات", "restart whatsapp", "آخر الطلبات"],
        "pharmacy": ["إحصائياتي", "اقترح رد على عميل", "سعر البنادول", "بديل الأموكسيسيلين"],
        "customer": ["عايز حاجة للصداع", "سعر البنادول", "بديل الدواء", "أعمل أوردر"],
    }
    return {"role": role, "examples": examples.get(role, [])}
