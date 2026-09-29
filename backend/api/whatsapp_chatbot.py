"""
WhatsApp Chatbot Webhook — يستخدم ChatbotCore
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import structlog

from chatbot.core import get_core

logger = structlog.get_logger()
router = APIRouter(prefix="/webhook/whatsapp", tags=["whatsapp-chatbot"])


class WhatsAppMessage(BaseModel):
    from_phone: str
    from_name: str = ""
    message: str
    whatsapp_id: str = ""
    pharmacy_id: Optional[str] = None


class WhatsAppReply(BaseModel):
    to: str
    reply: str
    session_id: str
    tools_used: list[str] = []
    latency_ms: int = 0


@router.post("/chat", response_model=WhatsAppReply)
async def whatsapp_chatbot(req: WhatsAppMessage):
    logger.info("whatsapp.incoming",
                from_phone=req.from_phone[:5] + "***",
                message_len=len(req.message))

    try:
        core = get_core()
        response = await core.chat(
            message=req.message,
            channel="whatsapp",
            channel_user_id=req.from_phone,
            pharmacy_id=req.pharmacy_id,
        )

        logger.info("whatsapp.replied",
                    session_id=response.session_id,
                    tools=len(response.tool_calls),
                    latency_ms=response.latency_ms)

        return WhatsAppReply(
            to=req.from_phone,
            reply=response.text,
            session_id=response.session_id,
            tools_used=[t["name"] for t in response.tool_calls],
            latency_ms=response.latency_ms,
        )
    except Exception as e:
        logger.error("whatsapp.failed", error=str(e)[:300])
        raise HTTPException(status_code=500, detail="حصلت مشكلة في الشات")


@router.get("/health")
async def health():
    return {"status": "ok"}
