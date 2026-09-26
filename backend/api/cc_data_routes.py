"""Control Center Data Routes — Admin + AI + Infrastructure."""
from __future__ import annotations
import os
import subprocess
import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from auth.dependencies import require_admin
from auth.models import User
from db import SessionLocal

import structlog
logger = structlog.get_logger()
router = APIRouter(prefix="/v1/cc", tags=["control-center"])


# ═══════════════════════════════════════════════════════════════════
# 🤖 AI Monitoring
# ═══════════════════════════════════════════════════════════════════

@router.get("/ai/llm-stats")
async def ai_llm_stats(user: User = Depends(require_admin)):
    """إحصائيات استدعاءات LLM."""
    from api.monitoring_routes import _metrics
    calls = list(_metrics["llm_calls"])
    durations = [c.get("duration_ms", 0) for c in calls]
    return {
        "total": len(calls),
        "avg_ms": round(sum(durations) / len(durations), 2) if durations else 0,
        "max_ms": max(durations) if durations else 0,
        "min_ms": min(durations) if durations else 0,
        "by_model": {},
        "recent": calls[-30:],
    }


@router.get("/ai/tool-stats")
async def ai_tool_stats(user: User = Depends(require_admin)):
    """إحصائيات استدعاءات الأدوات."""
    from api.monitoring_routes import _metrics
    calls = list(_metrics["tool_calls"])
    by_tool = {}
    for c in calls:
        t = c.get("tool", "unknown")
        if t not in by_tool:
            by_tool[t] = {"count": 0, "success": 0, "fail": 0, "avg_ms": 0, "total_ms": 0}
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
        "total": len(calls),
        "by_tool": by_tool,
        "recent": calls[-30:],
    }


@router.get("/ai/chat-activity")
async def ai_chat_activity(
    limit: int = Query(50, le=200),
    user: User = Depends(require_admin),
):
    """آخر محادثات."""
    from api.monitoring_routes import _metrics
    return {
        "total": len(_metrics["chat_activity"]),
        "recent": list(_metrics["chat_activity"])[-limit:],
    }


# ═══════════════════════════════════════════════════════════════════
# 🐳 Infrastructure
# ═══════════════════════════════════════════════════════════════════

def _run_cmd(cmd: list[str], timeout: int = 10) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr)[:5000]
    except subprocess.TimeoutExpired:
        return -1, "⏱️ انتهت المهلة"
    except Exception as e:
        return -1, f"❌ {e}"


@router.get("/infra/docker")
async def infra_docker(user: User = Depends(require_admin)):
    """حالة الـ Docker containers."""
    code, out = _run_cmd([
        "docker", "ps", "-a",
        "--format", "{{.Names}}|{{.Image}}|{{.Status}}|{{.Ports}}"
    ], timeout=5)
    containers = []
    if code == 0:
        for line in out.strip().split("\n"):
            if not line.strip():
                continue
            parts = line.split("|")
            if len(parts) >= 4:
                containers.append({
                    "name": parts[0],
                    "image": parts[1],
                    "status": parts[2],
                    "ports": parts[3],
                })
    return {"containers": containers, "error": out if code != 0 else None}


@router.get("/infra/services")
async def infra_services(user: User = Depends(require_admin)):
    """حالة الـ systemd services."""
    services = [
        "h1ai", "ssh", "docker", "redis-server", "postgresql",
        "nginx", "tailscaled", "fail2ban", "suricata",
    ]
    result = {}
    for svc in services:
        code, out = _run_cmd(["systemctl", "is-active", svc], timeout=2)
        result[svc] = out.strip() or "unknown"
    return {"services": result}


@router.get("/infra/network")
async def infra_network(user: User = Depends(require_admin)):
    """الاتصالات والـ ports."""
    code, out = _run_cmd(["ss", "-tlnp"], timeout=3)
    ports = []
    if code == 0:
        for line in out.split("\n")[1:]:
            parts = line.split()
            if len(parts) >= 4:
                ports.append({
                    "state": parts[0],
                    "local": parts[3],
                    "process": parts[-1] if len(parts) > 4 else "—",
                })
    return {"ports": ports[:50]}


@router.get("/infra/processes")
async def infra_processes(user: User = Depends(require_admin)):
    """أعلى 15 process في CPU و RAM."""
    import psutil
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent', 'status']):
        try:
            info = p.info
            info['cpu'] = round(info.get('cpu_percent') or 0, 2)
            info['mem'] = round(info.get('memory_percent') or 0, 2)
            procs.append(info)
        except Exception:
            continue
    top_cpu = sorted(procs, key=lambda x: -x['cpu'])[:15]
    top_mem = sorted(procs, key=lambda x: -x['mem'])[:15]
    return {
        "top_cpu": top_cpu,
        "top_mem": top_mem,
        "total": len(procs),
    }


@router.get("/infra/disk")
async def infra_disk(user: User = Depends(require_admin)):
    """استخدام الـ disk."""
    import psutil
    parts = []
    for p in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(p.mountpoint)
            parts.append({
                "device": p.device,
                "mountpoint": p.mountpoint,
                "fstype": p.fstype,
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "percent": usage.percent,
            })
        except Exception:
            continue
    return {"partitions": parts}


# ═══════════════════════════════════════════════════════════════════
# 📦 Admin Data
# ═══════════════════════════════════════════════════════════════════

@router.get("/admin/products")
async def admin_products(
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=200),
    search: str = Query(""),
    user: User = Depends(require_admin),
):
    """قائمة المنتجات."""
    db = SessionLocal()
    try:
        from sqlalchemy import text
        offset = (page - 1) * size
        q = f"""
            SELECT "ItemCode", "ItemName", "Category", "Price", "StockQty"
            FROM products
            {"WHERE LOWER(\"ItemName\") LIKE :s OR LOWER(\"ItemCode\") LIKE :s" if search else ""}
            ORDER BY "ItemCode"
            LIMIT :l OFFSET :o
        """
        params = {"l": size, "o": offset}
        if search:
            params["s"] = f"%{search.lower()}%"
        rows = db.execute(text(q), params).fetchall()
        total = db.execute(text("SELECT COUNT(*) FROM products")).scalar() or 0
        return {
            "items": [dict(r._mapping) for r in rows],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
        }
    except Exception as e:
        return {"items": [], "total": 0, "error": str(e)}
    finally:
        db.close()


@router.get("/admin/drugs")
async def admin_drugs(
    page: int = Query(1, ge=1),
    size: int = Query(25, ge=1, le=200),
    search: str = Query(""),
    user: User = Depends(require_admin),
):
    """قائمة الأدوية."""
    db = SessionLocal()
    try:
        from sqlalchemy import text
        offset = (page - 1) * size
        q = f"""
            SELECT * FROM drugs
            {"WHERE LOWER(name) LIKE :s OR LOWER(generic_name) LIKE :s" if search else ""}
            ORDER BY id
            LIMIT :l OFFSET :o
        """
        params = {"l": size, "o": offset}
        if search:
            params["s"] = f"%{search.lower()}%"
        rows = db.execute(text(q), params).fetchall()
        total = db.execute(text("SELECT COUNT(*) FROM drugs")).scalar() or 0
        return {
            "items": [dict(r._mapping) for r in rows],
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size,
        }
    except Exception as e:
        return {"items": [], "total": 0, "error": str(e)}
    finally:
        db.close()


@router.get("/admin/conditions")
async def admin_conditions(user: User = Depends(require_admin)):
    """قائمة الحالات الطبية."""
    db = SessionLocal()
    try:
        from sqlalchemy import text
        rows = db.execute(text("SELECT * FROM conditions ORDER BY id LIMIT 100")).fetchall()
        return {"items": [dict(r._mapping) for r in rows]}
    except Exception as e:
        return {"items": [], "error": str(e)}
    finally:
        db.close()


@router.get("/admin/stats")
async def admin_stats(user: User = Depends(require_admin)):
    """إحصائيات قاعدة البيانات."""
    db = SessionLocal()
    try:
        from sqlalchemy import text
        tables = ["products", "drugs", "conditions", "interactions", "synonyms", "users"]
        stats = {}
        for t in tables:
            try:
                cnt = db.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar() or 0
                stats[t] = cnt
            except Exception:
                stats[t] = "—"
        db_size = db.execute(text("SELECT pg_database_size(current_database())")).scalar()
        return {
            "tables": stats,
            "db_size_mb": round(db_size / (1024**2), 2) if db_size else 0,
        }
    except Exception as e:
        return {"tables": {}, "error": str(e)}
    finally:
        db.close()
