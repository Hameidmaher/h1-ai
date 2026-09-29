"""Control Routes — تحكم كامل بالمشروع."""
from __future__ import annotations
import os
import subprocess
import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth.dependencies import require_admin
from auth.models import User

import structlog
logger = structlog.get_logger()
router = APIRouter(prefix="/v1/control", tags=["control"])


class ActionResult(BaseModel):
    success: bool
    message: str
    output: Optional[str] = None
    duration_ms: Optional[float] = None


def _run_cmd(cmd: list[str], timeout: int = 30) -> tuple[bool, str, float]:
    """يشغّل أمر shell ويرجّع (نجاح، مخرجات، مدة)."""
    import time
    start = time.time()
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        duration = (time.time() - start) * 1000
        ok = result.returncode == 0
        out = (result.stdout + result.stderr)[:2000]
        return ok, out, duration
    except subprocess.TimeoutExpired:
        return False, f"⏱️ انتهت المهلة ({timeout}s)", (time.time() - start) * 1000
    except Exception as e:
        return False, f"❌ خطأ: {e}", (time.time() - start) * 1000


@router.post("/restart", response_model=ActionResult)
async def restart_service(user: User = Depends(require_admin)):
    """إعادة تشغيل خدمة السيرفر."""
    logger.warning("control.restart", user=user.username)
    ok, out, dur = _run_cmd(["sudo", "systemctl", "restart", "h1ai.service"], timeout=30)
    return ActionResult(
        success=ok,
        message="✅ تم إعادة التشغيل" if ok else "❌ فشل إعادة التشغيل",
        output=out,
        duration_ms=round(dur, 2),
    )


@router.post("/clear-cache", response_model=ActionResult)
async def clear_cache(user: User = Depends(require_admin)):
    """تفريغ Redis cache."""
    logger.warning("control.clear_cache", user=user.username)
    ok, out, dur = _run_cmd(["redis-cli", "-p", "6381", "FLUSHALL"], timeout=10)
    if not ok:
        # جرّب البورت الافتراضي
        ok, out, dur = _run_cmd(["redis-cli", "FLUSHALL"], timeout=10)
    return ActionResult(
        success=ok,
        message="✅ تم تفريغ الـ cache" if ok else "❌ فشل",
        output=out,
        duration_ms=round(dur, 2),
    )


@router.post("/run-health-test", response_model=ActionResult)
async def run_health_test(user: User = Depends(require_admin)):
    """اختبار سريع للـ health."""
    logger.info("control.health_test", user=user.username)
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get("http://localhost:8000/health")
            return ActionResult(
                success=r.status_code == 200,
                message=f"✅ Health: {r.status_code}",
                output=r.text[:500],
            )
    except Exception as e:
        return ActionResult(success=False, message=f"❌ فشل: {e}")


@router.post("/backup-db", response_model=ActionResult)
async def backup_db(user: User = Depends(require_admin)):
    """نسخة احتياطية من قاعدة البيانات."""
    logger.warning("control.backup", user=user.username)
    backup_dir = os.path.expanduser("~/h1-ai/backups")
    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = f"{backup_dir}/db_backup_{ts}.sql"

    # PostgreSQL
    ok, out, dur = _run_cmd([
        "pg_dump", "-h", "localhost", "-p", "5434",
        "-U", "postgres", "-d", "h1ai",
        "-f", out_file
    ], timeout=120)
    return ActionResult(
        success=ok,
        message=f"✅ تم الحفظ: {out_file}" if ok else "❌ فشل النسخ",
        output=out or out_file,
        duration_ms=round(dur, 2),
    )


@router.post("/clear-logs", response_model=ActionResult)
async def clear_logs(user: User = Depends(require_admin)):
    """تفريغ ملفات الـ log."""
    logger.warning("control.clear_logs", user=user.username)
    paths = [
        "/var/log/h1ai.log",
        os.path.expanduser("~/h1-ai/backend/logs/h1ai-api.log"),
    ]
    cleared = []
    errors = []
    for p in paths:
        if os.path.exists(p):
            try:
                subprocess.run(["sudo", "truncate", "-s", "0", p], check=True, timeout=5)
                cleared.append(p)
            except Exception as e:
                errors.append(f"{p}: {e}")
    ok = len(errors) == 0
    return ActionResult(
        success=ok,
        message=f"✅ تم تفريغ {len(cleared)} ملف" if ok else f"⚠️ {len(errors)} خطأ",
        output="\n".join(cleared + errors),
    )


@router.get("/status")
async def service_status(user: User = Depends(require_admin)):
    """حالة الخدمات."""
    services = ["h1ai", "ssh", "docker", "redis-server", "postgresql", "nginx", "tailscaled"]
    status = {}
    for svc in services:
        try:
            r = subprocess.run(
                ["systemctl", "is-active", svc],
                capture_output=True, text=True, timeout=3
            )
            status[svc] = r.stdout.strip() or "unknown"
        except Exception:
            status[svc] = "error"
    return {"services": status, "timestamp": datetime.utcnow().isoformat()}


@router.get("/system-info")
async def system_info(user: User = Depends(require_admin)):
    """معلومات النظام."""
    import psutil
    boot = datetime.fromtimestamp(psutil.boot_time())
    uptime = (datetime.now() - boot).total_seconds()
    return {
        "hostname": os.uname().nodename,
        "os": os.uname().sysname + " " + os.uname().release,
        "python": os.sys.version.split()[0],
        "cpu_count": psutil.cpu_count(),
        "boot_time": boot.isoformat(),
        "uptime_seconds": int(uptime),
        "timestamp": datetime.utcnow().isoformat(),
    }
