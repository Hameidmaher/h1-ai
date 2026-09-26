"""Auth API — Login + Register + Profile."""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, Field
from pathlib import Path

from auth.jwt_handler import create_access_token, hash_password, verify_password
from auth.dependencies import get_current_user
from auth.models import User, UserInDB
from db import SessionLocal
from db.repositories import UserRepository

import structlog
logger = structlog.get_logger()
router = APIRouter(prefix="/v1/auth", tags=["auth-full"])


# ═══════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(...)
    password: str = Field(..., min_length=6, max_length=100)
    full_name: str = ""
    role: str = "customer"


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
    expires_in: int = 86400


# ═══════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════

@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest):
    """تسجيل مستخدم جديد."""
    db = SessionLocal()
    try:
        from sqlalchemy import text
        # نتأكد إن الإيميل مش موجود
        exists = db.execute(
            text("SELECT id FROM users WHERE LOWER(email) = LOWER(:e)"),
            {"e": req.email}
        ).fetchone()
        if exists:
            raise HTTPException(400, "الإيميل مستخدم بالفعل")

        # نتأكد إن الـ username مش موجود
        exists = db.execute(
            text("SELECT id FROM users WHERE LOWER(username) = LOWER(:u)"),
            {"u": req.username}
        ).fetchone()
        if exists:
            raise HTTPException(400, "اسم المستخدم مستخدم بالفعل")

        hashed = hash_password(req.password)
        role = req.role if req.role in ("customer", "pharmacist") else "customer"
        full_name = req.full_name or req.username

        row = db.execute(text("""
            INSERT INTO users (username, email, hashed_password, full_name, role, is_active)
            VALUES (:u, :e, :h, :f, :r, true)
            RETURNING id, username, email, full_name, role, is_active
        """), {"u": req.username, "e": req.email, "h": hashed, "f": full_name, "r": role}).fetchone()
        db.commit()

        if not row:
            raise HTTPException(500, "فشل إنشاء الحساب")

        user_dict = dict(row._mapping)
        token = create_access_token(
            user_id=str(user_dict["id"]),
            username=user_dict["username"],
            role=user_dict["role"],
        )

        logger.info("user.registered", username=user_dict["username"], role=user_dict["role"])

        return AuthResponse(
            access_token=token,
            user={**user_dict, "id": str(user_dict["id"])},
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error("register.failed", error=str(e))
        raise HTTPException(500, f"فشل التسجيل: {str(e)[:100]}")
    finally:
        db.close()


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    """تسجيل دخول."""
    db = SessionLocal()
    try:
        from sqlalchemy import text
        row = db.execute(text("""
            SELECT id, username, email, hashed_password, full_name, role, is_active
            FROM users
            WHERE LOWER(username) = LOWER(:u) OR LOWER(email) = LOWER(:u)
            LIMIT 1
        """), {"u": req.username}).fetchone()

        if not row:
            raise HTTPException(401, "اسم المستخدم أو كلمة المرور غلط")

        user = dict(row._mapping)
        if not user["is_active"]:
            raise HTTPException(403, "الحساب معطل")

        if not verify_password(req.password, user["hashed_password"]):
            raise HTTPException(401, "اسم المستخدم أو كلمة المرور غلط")

        token = create_access_token(
            user_id=str(user["id"]),
            username=user["username"],
            role=user["role"],
        )

        logger.info("user.login", username=user["username"], role=user["role"])

        return AuthResponse(
            access_token=token,
            user={
                "id": str(user["id"]),
                "username": user["username"],
                "email": user["email"],
                "full_name": user["full_name"] or user["username"],
                "role": user["role"],
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("login.failed", error=str(e))
        raise HTTPException(500, f"فشل الدخول: {str(e)[:100]}")
    finally:
        db.close()


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    """معلومات المستخدم الحالي."""
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
        "full_name": getattr(user, "full_name", ""),
        "pharmacy_id": getattr(user, "pharmacy_id", None),
    }
