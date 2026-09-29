from fastapi import APIRouter, Depends
from pydantic import BaseModel
from auth.dependencies import get_current_user
from auth.models import User
from integrations.whatsapp import whatsapp_service
from config_loader import prod_config

router = APIRouter(prefix="/v1/whatsapp", tags=["whatsapp"])


class ChatUrlRequest(BaseModel):
    message: str = ""


class ChatUrlResponse(BaseModel):
    url: str
    phone: str
    display_phone: str
    mode: str


@router.get("/info")
async def whatsapp_info():
    return {
        "enabled": prod_config.get("whatsapp.enabled", True),
        "phone": prod_config.whatsapp_phone,
        "display_phone": prod_config.get("whatsapp.display_phone", ""),
        "mode": prod_config.whatsapp_mode,
    }


@router.post("/chat-url", response_model=ChatUrlResponse)
async def get_chat_url(
    req: ChatUrlRequest,
    user: User = Depends(get_current_user),
):
    msg = req.message or "مرحباً، أحتاج مساعدة"
    url = whatsapp_service.build_chat_url(msg)
    return ChatUrlResponse(
        url=url,
        phone=prod_config.whatsapp_phone,
        display_phone=prod_config.get("whatsapp.display_phone", ""),
        mode=prod_config.whatsapp_mode,
    )
