"""Admin API keys routes — /v1/admin/api-keys."""
from uuid import uuid4
import hashlib
import secrets

from fastapi import APIRouter, Depends, Request
from sqlalchemy import text

from models.schemas import User
from auth.dependencies import require_admin
from db import SessionLocal

router = APIRouter(prefix="/v1/admin/api-keys", tags=["admin-api-keys"])


@router.get("")
async def list_api_keys(user: User = Depends(require_admin)):
    db = SessionLocal()
    try:
        result = db.execute(text("""
            SELECT a.id::text, a.name, a.key_prefix, a.scopes, a.is_active,
                   a.last_used_at, a.created_at, a.expires_at,
                   p.name_ar AS pharmacy_name
            FROM api_keys a
            LEFT JOIN pharmacies p ON p.id = a.pharmacy_id
            ORDER BY a.created_at DESC
        """))
        return {"keys": [dict(row._mapping) for row in result]}
    finally:
        db.close()


@router.post("")
async def create_api_key(request: Request, user: User = Depends(require_admin)):
    data = await request.json()

    raw_key = "h1ai_" + secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:12]

    db = SessionLocal()
    try:
        kid = str(uuid4())
        db.execute(text("""
            INSERT INTO api_keys (id, pharmacy_id, name, key_hash, key_prefix, scopes)
            VALUES (:id, :pid, :name, :hash, :prefix, :scopes)
        """), {
            "id": kid,
            "pid": data.get("pharmacy_id"),
            "name": data.get("name", "API Key"),
            "hash": key_hash,
            "prefix": key_prefix,
            "scopes": '["read", "write"]',
        })
        db.commit()

        return {
            "success": True,
            "id": kid,
            "key": raw_key,
            "prefix": key_prefix,
            "warning": "Save this key now — it won't be shown again",
        }
    finally:
        db.close()


@router.delete("/{key_id}")
async def delete_api_key(key_id: str, user: User = Depends(require_admin)):
    db = SessionLocal()
    try:
        db.execute(text("DELETE FROM api_keys WHERE id = :id"), {"id": key_id})
        db.commit()
        return {"success": True}
    finally:
        db.close()
