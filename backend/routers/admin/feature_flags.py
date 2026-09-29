"""Admin feature flags routes — /v1/admin/feature-flags."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy import text

from models.schemas import User
from auth.dependencies import require_admin
from db import SessionLocal

router = APIRouter(prefix="/v1/admin/feature-flags", tags=["admin-feature-flags"])


@router.get("")
async def list_feature_flags(user: User = Depends(require_admin)):
    """List all feature flags."""
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT id::text, key, name, description, is_enabled,
                   rollout_percentage, created_at
            FROM feature_flags
            ORDER BY key
        """))
        return {"flags": [dict(row._mapping) for row in result]}
    finally:
        db.close()


@router.put("/{flag_key}")
async def update_feature_flag(flag_key: str, request: Request, user: User = Depends(require_admin)):
    data = await request.json()
    db = SessionLocal()
    try:
        db.execute(text("""
            UPDATE feature_flags
            SET is_enabled = COALESCE(:enabled, is_enabled),
                rollout_percentage = COALESCE(:rollout, rollout_percentage),
                updated_at = NOW()
            WHERE key = :key
        """), {
            "enabled": data.get("is_enabled"),
            "rollout": data.get("rollout_percentage"),
            "key": flag_key,
        })
        db.commit()
        return {"success": True}
    finally:
        db.close()
