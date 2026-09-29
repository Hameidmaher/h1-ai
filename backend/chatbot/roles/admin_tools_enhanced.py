"""Admin Tools Enhanced — أدوات تقنية + إدارية."""
from __future__ import annotations
import subprocess, os
from pathlib import Path
from typing import Optional
import structlog

logger = structlog.get_logger()
H1AI_ROOT = Path.home() / "h1-ai"


async def _project_structure() -> dict:
    """بنية المشروع."""
    try:
        result = subprocess.run(
            ["find", str(H1AI_ROOT), "-maxdepth", "2", "-type", "d"],
            capture_output=True, text=True, timeout=5
        )
        dirs = [d.replace(str(H1AI_ROOT) + "/", "") for d in result.stdout.strip().split("\n")
                if d and ".git" not in d and "__pycache__" not in d and "node_modules" not in d]
        dirs = sorted(set(dirs))[:20]
        reply = "📁 **بنية المشروع:**\n\n```\n"
        for d in dirs:
            reply += f"{d}\n"
        reply += "```\n\n📊 " + str(len(dirs)) + " مجلد"
        return {"reply": reply, "data": {"dirs": dirs}, "tools_used": ["project_structure"]}
    except Exception as e:
        return {"reply": f"❌ {e}", "tools_used": ["project_structure"]}


async def _tech_stack() -> dict:
    """Stack التقني."""
    reply = (
        "🛠️ **Stack التقني:**\n\n"
        "**Backend:** Python 3.13 + FastAPI + Uvicorn\n"
        "**DB:** PostgreSQL 17 + Redis 8\n"
        "**AI:** Groq (llama-3.3-70b) + LangChain + LangGraph\n"
        "**WhatsApp:** Baileys (Node.js)\n"
        "**Frontend:** HTML/JS + Flutter\n"
        "**Infra:** Docker + systemd + Cloudflare Tunnel"
    )
    return {"reply": reply, "tools_used": ["tech_stack"]}


async def _architecture() -> dict:
    """البنية المعمارية."""
    reply = (
        "🏗️ **البنية المعمارية:**\n\n"
        "```\n"
        "Client (WhatsApp/Web)\n"
        "        ↓\n"
        "API Gateway (FastAPI)\n"
        "        ↓\n"
        "Orchestrator (LangGraph)\n"
        "   ↓    ↓    ↓\n"
        "Advisory Customer Pharmacist\n"
        "Engine   Agent    Agent\n"
        "(BM25)   (LC)     (LC)\n"
        "```\n\n"
        "**Components:**\n"
        "- **Orchestrator:** يوجّه الرسائل\n"
        "- **Advisory Engine:** بحث سريع بدون LLM\n"
        "- **Customer Agent:** استشارات\n"
        "- **Pharmacist Agent:** تقارير وأدوات"
    )
    return {"reply": reply, "tools_used": ["architecture"]}


async def _recent_errors() -> dict:
    """آخر الأخطاء."""
    try:
        result = subprocess.run(
            ["sudo", "journalctl", "-u", "h1ai.service", "-n", "60",
             "--no-pager", "-p", "err"],
            capture_output=True, text=True, timeout=5
        )
        errors = [l for l in result.stdout.split("\n") if l.strip()][-10:]
        if not errors:
            return {"reply": "✅ **لا أخطاء حديثة**", "tools_used": ["recent_errors"]}
        reply = f"⚠️ **آخر {len(errors)} أخطاء:**\n\n```\n"
        for e in errors:
            reply += e[:180] + "\n"
        reply += "```"
        return {"reply": reply, "tools_used": ["recent_errors"]}
    except Exception as e:
        return {"reply": f"❌ {e}", "tools_used": ["recent_errors"]}


async def _services_status() -> dict:
    """حالة الخدمات."""
    services = ["h1ai.service", "h1ai-whatsapp.service", "postgresql", "redis-server"]
    results = {}
    for svc in services:
        try:
            r = subprocess.run(["systemctl", "is-active", svc],
                             capture_output=True, text=True, timeout=3)
            results[svc] = r.stdout.strip()
        except Exception:
            results[svc] = "unknown"

    reply = "🛠️ **حالة الخدمات:**\n\n"
    icons = {"active": "🟢", "inactive": "🔴", "failed": "❌"}
    for svc, status in results.items():
        reply += f"{icons.get(status, '⚪')} **{svc}**: `{status}`\n"
    return {"reply": reply, "data": results, "tools_used": ["services_status"]}


async def _system_health() -> dict:
    """صحة النظام."""
    try:
        load = os.getloadavg()
        mem = subprocess.run(["free", "-h"], capture_output=True, text=True).stdout
        disk = subprocess.run(["df", "-h", "/"], capture_output=True, text=True).stdout
        mem_lines = mem.split("\n")[:3]
        disk_lines = disk.split("\n")[:2]
        reply = "💚 **صحة النظام:**\n\n"
        reply += f"**CPU Load:** `{load[0]:.2f}` / `{load[1]:.2f}` / `{load[2]:.2f}`\n\n"
        reply += "**Memory:**\n```\n" + "\n".join(mem_lines) + "\n```\n\n"
        reply += "**Disk:**\n```\n" + "\n".join(disk_lines) + "\n```"
        return {"reply": reply, "tools_used": ["system_health"]}
    except Exception as e:
        return {"reply": f"❌ {e}", "tools_used": ["system_health"]}


async def _explain_code(topic: str) -> dict:
    """اشرح جزء من الكود."""
    explanations = {
        "orchestrator": (
            "🎯 **Orchestrator** — `backend/core/orchestrator.py`\n\n"
            "**الدور:** يوجّه الرسائل للـ agent المناسب.\n\n"
            "**Flow:**\n"
            "1. استقبل الرسالة\n"
            "2. صنّف النية\n"
            "3. افحص Emergency (rule-based، <50ms)\n"
            "4. إذا emergency → رد فوري\n"
            "5. وإلا → وجّه للـ Agent"
        ),
        "advisory": (
            "📚 **Advisory Engine** — `backend/knowledge/engine.py`\n\n"
            "**التقنيات:** BM25 + RapidFuzz + Rules\n\n"
            "**Flow:** Query → BM25 → Rules → Top-k"
        ),
        "rag": (
            "🧠 **RAG:**\n\n"
            "1. Retrieval (BM25)\n"
            "2. Augmentation (+context)\n"
            "3. Generation (Groq LLM)\n\n"
            "**Sources:** drugs.json, interactions.json, symptoms.json"
        ),
        "whatsapp": (
            "📱 **WhatsApp Integration:**\n\n"
            "- Baileys (Node.js)\n"
            "- Multi-session\n"
            "- QR auth\n"
            "- Port 3001"
        ),
        "database": (
            "🗄️ **Database Schema:**\n\n"
            "**PostgreSQL:** users, pharmacies, products, drugs, interactions, chat_sessions, messages\n"
            "**Redis:** Sessions, Cache, Rate limit"
        ),
    }
    topic_lower = topic.lower()
    for key, exp in explanations.items():
        if key in topic_lower:
            return {"reply": exp, "tools_used": ["explain_code"]}
    return {
        "reply": "📖 **اسألني عن:**\n- orchestrator\n- advisory\n- rag\n- whatsapp\n- database\n\nمثال: 'اشرح orchestrator'",
        "tools_used": ["explain_code"]
    }


def detect_tech_tool(msg: str) -> Optional[str]:
    """كشف أداة تقنية."""
    msg_lower = msg.lower()
    tech_keywords = {
        "project_structure": ["بنية المشروع", "هيكل المشروع", "المجلدات", "structure"],
        "tech_stack": ["stack", "التقنيات", "بماذا مبني", "استخدم ايه"],
        "architecture": ["architecture", "البنية المعمارية", "كيف يعمل النظام"],
        "recent_errors": ["اخطاء", "أخطاء", "errors", "مشاكل تقنية", "فشل"],
        "services_status": ["حالة الخدمات", "services", "systemd"],
        "system_health": ["صحة النظام", "cpu", "ram", "disk", "الموارد", "performance"],
        "explain_code": ["اشرح", "explain", "orchestrator", "advisory", "rag", "whatsapp", "database"],
    }
    for tool, keywords in tech_keywords.items():
        if any(kw in msg_lower for kw in keywords):
            return tool
    return None


async def execute_tech(tool: str, message: str, context: dict) -> dict:
    """تنفيذ أداة تقنية."""
    handlers = {
        "project_structure": _project_structure,
        "tech_stack": _tech_stack,
        "architecture": _architecture,
        "recent_errors": _recent_errors,
        "services_status": _services_status,
        "system_health": _system_health,
        "explain_code": lambda: _explain_code(message),
    }
    handler = handlers.get(tool)
    if not handler:
        return {"reply": f"⚠️ أداة غير معروفة: {tool}", "tools_used": []}
    try:
        return await handler()
    except Exception as e:
        logger.error("tech_tool_failed", tool=tool, error=str(e))
        return {"reply": f"❌ خطأ في {tool}: {str(e)[:150]}", "tools_used": [tool]}
