"""Tunnel Control API — إدارة Cloudflare Tunnel"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import subprocess
import re
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/api/tunnel", tags=["tunnel"])

TUNNEL_CONTAINER_NAME = "h1ai-tunnel"

class TunnelStatus(BaseModel):
    running: bool
    url: str | None = None
    status_text: str = ""

def get_tunnel_url_from_logs() -> str | None:
    """استخراج عنوان URL من سجلات الـ container."""
    try:
        # شغّل الأمر لجلب آخر 100 سطر من السجلات
        result = subprocess.run(
            ["docker", "logs", "--tail", "100", TUNNEL_CONTAINER_NAME],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            logger.warning("tunnel.logs_failed", error=result.stderr[:200])
            return None
        
        # ابحث عن الرابط في السجلات
        # مثال: https://random-name.trycloudflare.com
        match = re.search(r'(https://[a-z0-9-]+\.trycloudflare\.com)', result.stdout)
        if match:
            return match.group(1)
        
        # جرّب نمط آخر إذا كان موجوداً
        match = re.search(r'(https://[a-z0-9-]+\.cfargotunnel\.com)', result.stdout)
        if match:
            return match.group(1)
            
        return None
    except Exception as e:
        logger.error("tunnel.url_extract_failed", error=str(e)[:200])
        return None

def is_tunnel_running() -> bool:
    """التحقق مما إذا كان الـ container يعمل."""
    try:
        result = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Running}}", TUNNEL_CONTAINER_NAME],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip().lower() == "true"
    except Exception:
        return False

@router.get("/status", response_model=TunnelStatus)
async def get_tunnel_status():
    """جلب حالة النفق الحالية."""
    running = is_tunnel_running()
    url = get_tunnel_url_from_logs() if running else None
    
    status_text = "يعمل" if running else "متوقف"
    
    return TunnelStatus(
        running=running,
        url=url,
        status_text=status_text
    )

@router.post("/start")
async def start_tunnel():
    """بدء تشغيل النفق."""
    try:
        result = subprocess.run(
            ["docker", "start", TUNNEL_CONTAINER_NAME],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            raise HTTPException(500, f"فشل بدء النفق: {result.stderr[:200]}")
        
        # انتظر بضع ثوانٍ لإنشاء الرابط
        import asyncio
        await asyncio.sleep(5)
        
        return {"success": True, "message": "تم بدء النفق بنجاح"}
    except Exception as e:
        logger.error("tunnel.start_failed", error=str(e)[:200])
        raise HTTPException(500, f"فشل بدء النفق: {str(e)[:100]}")

@router.post("/stop")
async def stop_tunnel():
    """إيقاف النفق."""
    try:
        result = subprocess.run(
            ["docker", "stop", TUNNEL_CONTAINER_NAME],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            raise HTTPException(500, f"فشل إيقاف النفق: {result.stderr[:200]}")
        
        return {"success": True, "message": "تم إيقاف النفق بنجاح"}
    except Exception as e:
        logger.error("tunnel.stop_failed", error=str(e)[:200])
        raise HTTPException(500, f"فشل إيقاف النفق: {str(e)[:100]}")

@router.post("/restart")
async def restart_tunnel():
    """إعادة تشغيل النفق."""
    try:
        subprocess.run(["docker", "stop", TUNNEL_CONTAINER_NAME], 
                      capture_output=True, timeout=30)
        subprocess.run(["docker", "start", TUNNEL_CONTAINER_NAME], 
                      capture_output=True, timeout=30)
        
        import asyncio
        await asyncio.sleep(5)
        
        return {"success": True, "message": "تم إعادة تشغيل النفق"}
    except Exception as e:
        logger.error("tunnel.restart_failed", error=str(e)[:200])
        raise HTTPException(500, f"فشل إعادة التشغيل: {str(e)[:100]}")
