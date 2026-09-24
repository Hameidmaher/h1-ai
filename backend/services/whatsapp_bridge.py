"""WhatsApp Bridge — communicate with WhatsApp service."""
from __future__ import annotations

import httpx
import structlog

logger = structlog.get_logger()

WHATSAPP_SERVICE_URL = "http://localhost:3001"


class WhatsAppBridge:
    """Bridge to the WhatsApp Multi-Session Service."""

    def __init__(self, base_url: str = WHATSAPP_SERVICE_URL):
        self.base_url = base_url

    async def health(self) -> dict:
        """Check WhatsApp service health."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{self.base_url}/health")
                return r.json()
        except Exception as e:
            logger.error("whatsapp.health_failed", error=str(e)[:200])
            return {"status": "unavailable", "error": str(e)[:200]}

    async def list_sessions(self) -> list:
        """List all WhatsApp sessions."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{self.base_url}/sessions")
                return r.json().get("sessions", [])
        except Exception as e:
            logger.error("whatsapp.list_failed", error=str(e)[:200])
            return []

    async def create_session(self, phone_number: str, pharmacy_id: str = None) -> dict:
        """Create a new WhatsApp session."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(
                    f"{self.base_url}/sessions",
                    json={"phone_number": phone_number, "pharmacy_id": pharmacy_id},
                )
                return r.json()
        except Exception as e:
            logger.error("whatsapp.create_failed", error=str(e)[:200])
            return {"error": str(e)[:200]}

    async def get_qr(self, phone_number: str) -> dict:
        """Get QR code for session."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"{self.base_url}/sessions/{phone_number}/qr")
                return r.json()
        except Exception as e:
            logger.error("whatsapp.qr_failed", error=str(e)[:200])
            return {"error": str(e)[:200]}

    async def delete_session(self, phone_number: str) -> dict:
        """Stop a session."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.delete(f"{self.base_url}/sessions/{phone_number}")
                return r.json()
        except Exception as e:
            return {"error": str(e)[:200]}


    async def disconnect_session(self, phone_number: str) -> dict:
        """Disconnect a session (keep files, logout only)."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(f"{self.base_url}/sessions/{phone_number}/disconnect")
                return r.json()
        except Exception as e:
            logger.error("whatsapp.disconnect_failed", error=str(e)[:200])
            return {"error": str(e)[:200]}

    async def send_message(self, phone_number: str, to: str, message: str) -> dict:
        """Send a message through a session."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(
                    f"{self.base_url}/send",
                    json={"phone_number": phone_number, "to": to, "message": message},
                )
                return r.json()
        except Exception as e:
            return {"error": str(e)[:200]}


whatsapp_bridge = WhatsAppBridge()
