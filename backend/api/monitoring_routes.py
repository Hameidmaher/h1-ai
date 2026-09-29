"""
Monitoring API — لوحة مراقبة حية للمشروع.
"""
from __future__ import annotations

import os
import time
import json
import psutil
from datetime import datetime, timedelta
from collections import deque, defaultdict
from typing import Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from auth.dependencies import require_admin, require_super_admin
from auth.models import User

import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/v1/monitoring", tags=["monitoring"])


# ═══════════════════════════════════════════════════════════════
# In-memory metrics (آخر 1000 طلب)
# ═══════════════════════════════════════════════════════════════
_metrics = {
    "requests": deque(maxlen=1000),
    "tool_calls": deque(maxlen=500),
    "llm_calls": deque(maxlen=500),
    "errors": deque(maxlen=200),
    "chat_activity": deque(maxlen=100),
}

_start_time = time.time()


def record_request(method: str, path: str, status: int, duration_ms: float):
    """يُسجّل طلب (يُستخدم في middleware)."""
    _metrics["requests"].append({
        "ts": time.time(),
        "method": method,
        "path": path,
        "status": status,
        "duration_ms": round(duration_ms, 2),
    })
    if status >= 500:
        _metrics["errors"].append({
            "ts": time.time(),
            "type": "http_5xx",
            "path": path,
            "status": status,
        })


# ═══════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════

@router.get("/system")
async def system_stats(user: User = Depends(require_admin)):
    """System stats — CPU, RAM, Disk."""
    cpu = psutil.cpu_percent(interval=0.5, percpu=True)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    net = psutil.net_io_counters()

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": int(time.time() - _start_time),
        "hostname": os.uname().nodename,
        "cpu": {
            "percent_total": round(sum(cpu) / len(cpu), 1),
            "percent_per_core": cpu,
            "count": psutil.cpu_count(),
            "load_avg": list(os.getloadavg()),
        },
        "memory": {
            "total_gb": round(mem.total / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "percent": mem.percent,
        },
        "disk": {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent": disk.percent,
        },
        "network": {
            "bytes_sent_mb": round(net.bytes_sent / (1024**2), 2),
            "bytes_recv_mb": round(net.bytes_recv / (1024**2), 2),
        },
    }


@router.get("/requests")
async def request_stats(user: User = Depends(require_admin)):
    """إحصائيات الطلبات — آخر 1000."""
    reqs = list(_metrics["requests"])
    now = time.time()

    # آخر دقيقة
    last_min = [r for r in reqs if now - r["ts"] < 60]
    # آخر 5 دقايق
    last_5min = [r for r in reqs if now - r["ts"] < 300]

    # آخر 10 ثواني
    last_10s = [r for r in reqs if now - r["ts"] < 10]

    durations = [r["duration_ms"] for r in reqs if r["duration_ms"]]

    # توزيع الـ endpoints
    by_path = defaultdict(lambda: {"count": 0, "errors": 0, "avg_ms": 0, "total_ms": 0})
    for r in reqs:
        p = r["path"]
        by_path[p]["count"] += 1
        by_path[p]["total_ms"] += r["duration_ms"]
        if r["status"] >= 400:
            by_path[p]["errors"] += 1

    # حساب المتوسط
    for p, data in by_path.items():
        if data["count"] > 0:
            data["avg_ms"] = round(data["total_ms"] / data["count"], 2)
        del data["total_ms"]

    # ترتيب حسب العدد
    top_paths = sorted(by_path.items(), key=lambda x: -x[1]["count"])[:15]

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total": len(reqs),
        "last_minute": len(last_min),
        "last_5min": len(last_5min),
        "last_10s": len(last_10s),
        "success": sum(1 for r in reqs if r["status"] < 400),
        "errors_4xx": sum(1 for r in reqs if 400 <= r["status"] < 500),
        "errors_5xx": sum(1 for r in reqs if r["status"] >= 500),
        "avg_ms": round(sum(durations) / len(durations), 2) if durations else 0,
        "max_ms": max(durations) if durations else 0,
        "min_ms": min(durations) if durations else 0,
        "top_endpoints": [
            {"path": p, **data} for p, data in top_paths
        ],
        "recent": list(_metrics["requests"])[-50:],
    }


@router.get("/tool-calls")
async def tool_calls(user: User = Depends(require_admin)):
    """آخر استدعاءات الأدوات."""
    calls = list(_metrics["tool_calls"])[-100:]
    by_tool = defaultdict(lambda: {"count": 0, "success": 0, "fail": 0, "avg_ms": 0, "total_ms": 0})
    for c in calls:
        t = c.get("tool", "unknown")
        by_tool[t]["count"] += 1
        if c.get("success"):
            by_tool[t]["success"] += 1
        else:
            by_tool[t]["fail"] += 1
        by_tool[t]["total_ms"] += c.get("duration_ms", 0)

    for t, d in by_tool.items():
        if d["count"] > 0:
            d["avg_ms"] = round(d["total_ms"] / d["count"], 2)
        del d["total_ms"]

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total": len(calls),
        "by_tool": dict(by_tool),
        "recent": list(_metrics["tool_calls"])[-30:],
    }


@router.get("/llm-calls")
async def llm_calls(user: User = Depends(require_admin)):
    """آخر استدعاءات LLM."""
    calls = list(_metrics["llm_calls"])[-100:]
    durations = [c.get("duration_ms", 0) for c in calls if c.get("duration_ms")]
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total": len(calls),
        "avg_ms": round(sum(durations) / len(durations), 2) if durations else 0,
        "by_model": dict(
            (m, sum(1 for c in calls if c.get("model") == m))
            for m in set(c.get("model", "unknown") for c in calls)
        ),
        "recent": calls[-30:],
    }


@router.get("/chat-activity")
async def chat_activity(user: User = Depends(require_admin)):
    """نشاط الـ chat — آخر 50 محادثة."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total": len(_metrics["chat_activity"]),
        "recent": list(_metrics["chat_activity"])[-50:],
    }


@router.get("/errors")
async def recent_errors(user: User = Depends(require_admin)):
    """آخر الأخطاء."""
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total": len(_metrics["errors"]),
        "recent": list(_metrics["errors"])[-50:],
    }


@router.get("/logs")
async def recent_logs(lines: int = 100, user: User = Depends(require_admin)):
    """آخر N سطر من log السيرفر."""
    lines = min(lines, 500)
    log_paths = [
        "/var/log/h1ai.log",
        os.path.expanduser("~/h1-ai/backend/logs/h1ai-api.log"),
    ]
    for path in log_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", errors="replace") as f:
                    all_lines = f.readlines()
                    recent = all_lines[-lines:]
                return {
                    "path": path,
                    "lines": recent,
                    "total": len(all_lines),
                }
            except Exception as e:
                continue
    return {"error": "لا يوجد ملف log متاح", "lines": []}


@router.get("/dashboard")
async def dashboard(user: User = Depends(require_admin)):
    """كل الإحصائيات في نداء واحد."""
    return {
        "system": await system_stats(user),
        "requests": await request_stats(user),
        "tool_calls": await tool_calls(user),
        "llm_calls": await llm_calls(user),
        "chat_activity": await chat_activity(user),
        "errors": await recent_errors(user),
    }


@router.get("/stream")
async def stream_metrics(user: User = Depends(require_admin)):
    """SSE stream — تحديثات حية كل 2 ثواني."""
    async def event_generator():
        while True:
            try:
                system = await system_stats(user)
                requests = await request_stats(user)
                yield f"event: metrics\ndata: {json.dumps({'system': system, 'requests': requests}, default=str)}\n\n"
                await asyncio.sleep(2)
            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
                await asyncio.sleep(5)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


import asyncio
