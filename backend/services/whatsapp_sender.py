"""WhatsApp Sender Service — إرسال رسائل نصية وأزرار تفاعلية."""
import os
import httpx
import structlog
from typing import List

logger = structlog.get_logger()

WHATSAPP_SERVICE_URL = os.getenv(
    "WHATSAPP_SERVICE_URL",
    "http://localhost:3001"
)


class WhatsAppSender:
    """إرسال رسائل WhatsApp عبر Baileys."""

    @staticmethod
    async def send_text(phone: str, text: str) -> dict:
        """إرسال رسالة نصية."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{WHATSAPP_SERVICE_URL}/send",
                    json={"phone": phone, "text": text},
                )
                return response.json()
        except Exception as e:
            logger.error("whatsapp.send_text_failed", error=str(e)[:200])
            return {"success": False, "error": str(e)}

    @staticmethod
    async def send_buttons(
        phone: str,
        text: str,
        buttons: List[dict],
        footer: str = "",
    ) -> dict:
        """إرسال رسالة بأزرار تفاعلية."""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    f"{WHATSAPP_SERVICE_URL}/send-buttons",
                    json={
                        "phone": phone,
                        "text": text,
                        "buttons": buttons,
                        "footer": footer,
                    },
                )
                return response.json()
        except Exception as e:
            logger.error("whatsapp.send_buttons_failed", error=str(e)[:200])
            return {"success": False, "error": str(e)}


whatsapp_sender = WhatsAppSender()
