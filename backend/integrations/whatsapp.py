from __future__ import annotations
import urllib.parse
from typing import Optional
import structlog
from config_loader import prod_config

logger = structlog.get_logger()


class WhatsAppService:
    def __init__(self):
        self.phone = prod_config.whatsapp_phone
        self.mode = prod_config.whatsapp_mode

    def build_chat_url(self, message: str = "") -> str:
        target = self.phone.replace("+", "").replace(" ", "")
        if not target:
            return ""
        if not message:
            return f"https://wa.me/{target}"
        text = urllib.parse.quote(message)
        return f"https://wa.me/{target}?text={text}"


whatsapp_service = WhatsAppService()
