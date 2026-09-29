"""WhatsApp Client — wrapper for the Node.js WhatsApp service.

Communicates with the Node.js service at http://localhost:3000/send
"""
from __future__ import annotations
import os
from typing import Optional
import httpx
import structlog

logger = structlog.get_logger()


class WhatsAppClient:
    """Client for WhatsApp Service (Node.js)."""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 10.0,
    ):
        self.base_url = base_url or os.getenv(
            "WHATSAPP_SERVICE_URL",
            "http://localhost:3000"
        )
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None
    
    @property
    def client(self) -> httpx.Client:
        if self._client is None:
            self._client = httpx.Client(timeout=self.timeout)
        return self._client
    
    def is_available(self) -> bool:
        """Check if WhatsApp service is up."""
        try:
            r = self.client.get(f"{self.base_url}/health", timeout=2.0)
            return r.status_code == 200
        except Exception as e:
            logger.debug("whatsapp_client.health_failed", error=str(e)[:100])
            return False
    
    def get_status(self) -> dict:
        """Get service status."""
        try:
            r = self.client.get(f"{self.base_url}/health", timeout=2.0)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return {"status": "unavailable"}
    
    def send_message(
        self,
        to: str,
        text: str,
    ) -> dict:
        """Send a WhatsApp message.
        
        Args:
            to: Phone number (e.g., +201234567890)
            text: Message text
        
        Returns:
            dict: {success: bool, message_id: str, error: str}
        """
        # Normalize phone
        phone = to.strip()
        if not phone.startswith("+"):
            phone = "+" + phone
        
        try:
            r = self.client.post(
                f"{self.base_url}/send",
                json={"to": phone, "text": text},
                timeout=self.timeout,
            )
            
            if r.status_code == 200:
                data = r.json()
                logger.info(
                    "whatsapp_client.sent",
                    to=phone,
                    length=len(text),
                )
                return {
                    "success": True,
                    "message_id": data.get("message_id", ""),
                    "data": data,
                }
            else:
                logger.warning(
                    "whatsapp_client.send_failed",
                    to=phone,
                    status=r.status_code,
                    body=r.text[:200],
                )
                return {
                    "success": False,
                    "error": f"HTTP {r.status_code}: {r.text[:200]}",
                }
        
        except httpx.ConnectError as e:
            logger.error("whatsapp_client.connect_error", error=str(e)[:100])
            return {
                "success": False,
                "error": "WhatsApp service not reachable",
            }
        except Exception as e:
            logger.error("whatsapp_client.unexpected", error=str(e)[:200])
            return {"success": False, "error": str(e)[:200]}
    
    def close(self):
        if self._client:
            self._client.close()
            self._client = None


# Singleton
whatsapp_client = WhatsAppClient()
