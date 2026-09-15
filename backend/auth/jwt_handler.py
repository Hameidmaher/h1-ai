"""JWT Handler — hardened, Python 3.13 compatible.

Uses argon2-cffi directly (passlib is unmaintained since 2020).
"""
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from auth.models import TokenPayload
from config import settings
import structlog
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, InvalidHashError

logger = structlog.get_logger()

# ═══ Password hasher (argon2) ═══
ph = PasswordHasher(
    time_cost=2,
    memory_cost=102400,  # 100 MB
    parallelism=8,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """Hash password with argon2id."""
    if not isinstance(password, str):
        raise ValueError("Password must be a string")
    if len(password) < 6:
        raise ValueError("Password too short (min 6)")
    if len(password) > 128:
        raise ValueError("Password too long (max 128)")
    return ph.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against argon2 hash."""
    if not plain or not hashed:
        return False
    try:
        ph.verify(hashed, plain)
        return True
    except VerifyMismatchError:
        return False
    except InvalidHashError as e:
        logger.warning("password.invalid_hash", error=str(e)[:100])
        return False
    except Exception as e:
        logger.warning("password.verify_failed", error=str(e)[:100])
        return False


def needs_rehash(hashed: str) -> bool:
    """Check if hash needs rehashing (params changed)."""
    try:
        return ph.check_needs_rehash(hashed)
    except Exception:
        return True


# ═══ JWT ═══
def _encode_token(payload: dict) -> str:
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_access_token(user_id: str, username: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "access",
    }
    return _encode_token(payload)


def create_refresh_token(user_id: str, username: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.jwt_refresh_token_expire_days)
    payload = {
        "sub": str(user_id),
        "username": username,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "type": "refresh",
    }
    return _encode_token(payload)


def decode_token(token: str) -> TokenPayload | None:
    """Decode and validate JWT — strict mode."""
    if not token or not isinstance(token, str):
        return None
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={
                "require": ["exp", "sub", "type"],
                "verify_exp": True,
                "verify_signature": True,
                "verify_aud": False,
            },
        )
        return TokenPayload(**payload)
    except JWTError as e:
        logger.warning("jwt.decode_failed", error=str(e)[:100])
        return None
    except Exception as e:
        logger.error("jwt.decode_unexpected", error=str(e)[:100])
        return None
