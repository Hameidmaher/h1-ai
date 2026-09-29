"""WhatsApp OTP Authentication — Login/Register عبر واتساب."""
from __future__ import annotations
import os
import random
import re
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from db import SessionLocal
from auth.jwt_handler import create_access_token
from auth.models import User
from auth.dependencies import require_admin

import structlog
logger = structlog.get_logger()
router = APIRouter(prefix="/v1/auth/whatsapp", tags=["whatsapp-auth"])


class SendOTPRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)
    country_code: str = Field("20", max_length=5)


class VerifyOTPRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)
    code: str = Field(..., min_length=6, max_length=6)
    country_code: str = Field("20", max_length=5)
    full_name: str = ""


class OTPResponse(BaseModel):
    success: bool
    message: str
    phone: Optional[str] = None
    dev_code: Optional[str] = None


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
    is_new_user: bool = False


def _normalize_phone(phone: str, cc: str = "20") -> str:
    digits = re.sub(r"\D", "", phone)
    cc = re.sub(r"\D", "", cc) or "20"
    if digits.startswith("0"):
        digits = digits[1:]
    if not digits.startswith(cc):
        digits = cc + digits
    return f"+{digits}"


def _generate_code() -> str:
    return f"{random.randint(0, 999999):06d}"


def _cfg():
    return {
        "dev_mode": os.getenv("WHATSAPP_DEV_MODE", "false").lower() == "true",
        "expiry_seconds": int(os.getenv("OTP_EXPIRY_SECONDS", "300")),
        "max_attempts": int(os.getenv("OTP_MAX_ATTEMPTS", "3")),
        "rate_limit_per_hour": int(os.getenv("OTP_RATE_LIMIT_PER_HOUR", "3")),
        "bridge_url": os.getenv("WHATSAPP_BRIDGE_URL", "http://localhost:3001"),
    }


def _check_rate_limit(db, phone: str, limit: int) -> bool:
    from sqlalchemy import text
    row = db.execute(text("""
        SELECT COUNT(*) FROM otp_codes
        WHERE phone = :p AND created_at > NOW() - INTERVAL '1 hour'
    """), {"p": phone}).scalar() or 0
    return row < limit


def _send_whatsapp_message(phone: str, message: str) -> tuple[bool, str]:
    cfg = _cfg()
    if cfg["dev_mode"]:
        logger.warning("whatsapp.dev_mode", phone=phone, message=message[:100])
        return True, "dev_mode"
    try:
        import httpx
        with httpx.Client(timeout=10) as client:
            for path in [f"/send", f"/api/send", f"/sessions/{phone}/send"]:
                try:
                    r = client.post(f"{cfg['bridge_url']}{path}",
                                    json={"to": phone, "phone": phone, "message": message, "text": message})
                    if r.status_code == 200:
                        return True, "sent"
                except Exception:
                    continue
        return False, "failed"
    except Exception as e:
        logger.error("whatsapp.send_failed", error=str(e)[:200])
        return False, str(e)[:200]


def _find_or_create_user(db, phone: str, full_name: str = "") -> tuple[dict, bool]:
    from sqlalchemy import text
    row = db.execute(text("""
        SELECT id, username, email, full_name, role, is_active
        FROM users WHERE username = :p OR phone = :p LIMIT 1
    """), {"p": phone}).fetchone()

    if row:
        user = dict(row._mapping)
        if not user["is_active"]:
            raise HTTPException(403, "الحساب معطل")
        return user, False

    user_id = str(uuid.uuid4())
    display_name = full_name.strip() or f"مستخدم {phone[-4:]}"

    # ✅ نتأكد من كل الحقول NOT NULL
    db.execute(text("""
        INSERT INTO users (
            id, username, email, phone, hashed_password, full_name, role,
            is_active, is_verified, created_at, updated_at
        ) VALUES (
            :id, :u, NULL, :p, '!whatsapp_otp_only', :f, 'customer',
            true, true, NOW(), NOW()
        )
    """), {"id": user_id, "u": phone, "f": display_name, "p": phone})
    db.commit()
    logger.info("whatsapp.user_created", phone=phone, user_id=user_id)

    return {
        "id": user_id, "username": phone, "email": None,
        "full_name": display_name, "role": "customer", "is_active": True,
    }, True


@router.post("/send-otp", response_model=OTPResponse)
async def send_otp(req: SendOTPRequest):
    cfg = _cfg()
    phone = _normalize_phone(req.phone, req.country_code)
    db = SessionLocal()
    try:
        if not _check_rate_limit(db, phone, cfg["rate_limit_per_hour"]):
            raise HTTPException(429, f"تجاوزت الحد ({cfg['rate_limit_per_hour']} رسائل/ساعة)")

        code = _generate_code()
        expires_at = datetime.utcnow() + timedelta(seconds=cfg["expiry_seconds"])

        from sqlalchemy import text
        db.execute(text("""
            INSERT INTO otp_codes (id, phone, code, expires_at, created_at)
            VALUES (:id, :p, :c, :e, NOW())
        """), {"id": str(uuid.uuid4()), "p": phone, "c": code, "e": expires_at})
        db.commit()

        message = f"🔐 كود H1-AI:\n\n*{code}*\n\nصالح 5 دقائق."
        sent, reason = _send_whatsapp_message(phone, message)

        return OTPResponse(
            success=True,
            message="✅ تم إرسال الكود" if not cfg["dev_mode"] else "🔧 Dev Mode",
            phone=phone,
            dev_code=code if cfg["dev_mode"] else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("send_otp.failed", error=str(e))
        raise HTTPException(500, f"فشل: {str(e)[:100]}")
    finally:
        db.close()


@router.post("/verify-otp", response_model=AuthResponse)
async def verify_otp(req: VerifyOTPRequest):
    cfg = _cfg()
    phone = _normalize_phone(req.phone, req.country_code)
    db = SessionLocal()
    try:
        from sqlalchemy import text
        row = db.execute(text("""
            SELECT id, code, expires_at, attempts FROM otp_codes
            WHERE phone = :p AND verified = false
            ORDER BY created_at DESC LIMIT 1
        """), {"p": phone}).fetchone()

        if not row:
            raise HTTPException(400, "مفيش كود نشط")
        otp = dict(row._mapping)

        if datetime.utcnow() > otp["expires_at"]:
            db.execute(text("UPDATE otp_codes SET verified = true WHERE id = :id"), {"id": otp["id"]})
            db.commit()
            raise HTTPException(400, "انتهت الصلاحية")

        if otp["attempts"] >= cfg["max_attempts"]:
            db.execute(text("UPDATE otp_codes SET verified = true WHERE id = :id"), {"id": otp["id"]})
            db.commit()
            raise HTTPException(400, f"تجاوزت {cfg['max_attempts']} محاولات")

        if otp["code"] != req.code:
            db.execute(text("UPDATE otp_codes SET attempts = attempts + 1 WHERE id = :id"), {"id": otp["id"]})
            db.commit()
            remaining = cfg["max_attempts"] - otp["attempts"] - 1
            raise HTTPException(400, f"كود غلط. باقي {remaining}")

        db.execute(text("UPDATE otp_codes SET verified = true WHERE id = :id"), {"id": otp["id"]})
        db.commit()

        user, is_new = _find_or_create_user(db, phone, req.full_name)
        token = create_access_token(user_id=str(user["id"]), username=user["username"], role=user["role"])

        return AuthResponse(
            access_token=token,
            user={
                "id": str(user["id"]), "username": user["username"],
                "email": user.get("email"), "phone": phone,
                "full_name": user.get("full_name") or user["username"],
                "role": user["role"],
            },
            is_new_user=is_new,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("verify.failed", error=str(e))
        raise HTTPException(500, f"فشل: {str(e)[:100]}")
    finally:
        db.close()


@router.get("/status")
async def status():
    cfg = _cfg()
    return {
        "dev_mode": cfg["dev_mode"],
        "expiry_seconds": cfg["expiry_seconds"],
        "max_attempts": cfg["max_attempts"],
        "rate_limit_per_hour": cfg["rate_limit_per_hour"],
    }
