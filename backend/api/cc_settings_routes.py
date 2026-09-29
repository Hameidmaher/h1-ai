"""Control Center — Settings API."""
import os
from fastapi import APIRouter, Depends, Body
from pydantic import BaseModel
from auth.dependencies import require_admin, require_super_admin
from auth.models import User
from db import SessionLocal
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/v1/cc/settings", tags=["cc-settings"])

_FEATURES_FILE = "/tmp/h1ai_features.json"

_DEFAULT_FEATURES = {
    "chat_enabled": True,
    "whatsapp_enabled": True,
    "voice_enabled": True,
    "streaming_enabled": True,
    "analytics_enabled": True,
    "maintenance_mode": False,
}


def _load_features() -> dict:
    import json
    f = dict(_DEFAULT_FEATURES)
    if os.path.exists(_FEATURES_FILE):
        try:
            with open(_FEATURES_FILE) as fh:
                f.update(json.load(fh))
        except Exception:
            pass
    return f


def _save_features(feats: dict):
    import json
    with open(_FEATURES_FILE, "w") as fh:
        json.dump(feats, fh, indent=2)


@router.get("/env")
async def get_env(user: User = Depends(require_super_admin)):
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    if not os.path.exists(env_path):
        return {"error": "الملف غير موجود", "path": env_path}
    settings = {}
    sensitive = ("KEY", "SECRET", "PASSWORD", "TOKEN")
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip(); v = v.strip().strip('"').strip("'")
            if any(s in k.upper() for s in sensitive):
                v = (v[:8] + "..." + v[-4:]) if len(v) > 12 else "***"
            settings[k] = v
    return {"settings": settings, "path": env_path}


@router.get("/db")
async def get_db(user: User = Depends(require_super_admin)):
    db = SessionLocal()
    try:
        from sqlalchemy import text
        version = db.execute(text("SELECT version()")).scalar()
        size = db.execute(text("SELECT pg_database_size(current_database())")).scalar()
        db_name = db.execute(text("SELECT current_database()")).scalar()
        conns = db.execute(text("SELECT count(*) FROM pg_stat_activity")).scalar()
        return {
            "version": (version or "—")[:80],
            "database": db_name,
            "size_mb": round(size / (1024**2), 2) if size else 0,
            "connections": conns,
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        db.close()


@router.get("/rate-limits")
async def get_rate_limits(user: User = Depends(require_admin)):
    try:
        from config import settings
        return {
            "chat": getattr(settings, "rate_limit_chat", "—"),
            "auth": getattr(settings, "rate_limit_auth", "—"),
        }
    except Exception as e:
        return {"error": str(e)}


# ═══ Features ═══
@router.get("/features")
async def get_features(user: User = Depends(require_admin)):
    return _load_features()


class FeatureUpdate(BaseModel):
    name: str
    enabled: bool


@router.post("/features/toggle")
async def toggle_feature(body: FeatureUpdate, user: User = Depends(require_super_admin)):
    feats = _load_features()
    feats[body.name] = body.enabled
    _save_features(feats)
    logger.warning("feature.toggle", user=user.username, name=body.name, enabled=body.enabled)
    return {"success": True, "features": feats}
