"""Auth dependencies — DB-backed."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from auth.models import User, UserInDB
from auth.jwt_handler import decode_token
from db import SessionLocal
from db.repositories import UserRepository
from typing import Optional

security = HTTPBearer(auto_error=False)


def _get_user_from_db(user_id: str) -> Optional[UserInDB]:
    """Fetch user from DB."""
    db = SessionLocal()
    try:
        repo = UserRepository(db)
        db_user = repo.get_by_id(user_id)
        if not db_user:
            return None
        return UserInDB(
            id=db_user.id,
            username=db_user.username,
            role=db_user.role,
            full_name=db_user.full_name or "",
            is_active=db_user.is_active,
            hashed_password=db_user.hashed_password,
        )
    finally:
        db.close()


def _get_user_by_username(username: str) -> Optional[UserInDB]:
    db = SessionLocal()
    try:
        repo = UserRepository(db)
        db_user = repo.get_by_username(username)
        if not db_user:
            return None
        return UserInDB(
            id=db_user.id,
            username=db_user.username,
            role=db_user.role,
            full_name=db_user.full_name or "",
            is_active=db_user.is_active,
            hashed_password=db_user.hashed_password,
        )
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# Backward-compatible wrappers
# ═══════════════════════════════════════════════════════════

def seed_users():
    """Deprecated — DB seeded via scripts/seed_database.py."""
    pass


def get_user_by_username(username: str) -> Optional[UserInDB]:
    return _get_user_by_username(username)


def get_user_by_id(user_id: str) -> Optional[UserInDB]:
    return _get_user_from_db(user_id)


async def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(security),
) -> User:
    if creds is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_token(creds.credentials)
    if payload is None or payload.type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user_db = get_user_by_id(payload.sub)
    if not user_db or not user_db.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return User(**user_db.model_dump(exclude={"hashed_password"}))


async def require_pharmacist(user: User = Depends(get_current_user)) -> User:
    if user.role not in ("pharmacist", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="هذه العملية متاحة للصيادلة فقط",
        )
    return user


async def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="هذه العملية متاحة للمدير فقط",
        )
    return user


# Backward compat: _users_db attribute
class _UsersDBProxy:
    """Proxy to mimic old _users_db."""
    def values(self):
        db = SessionLocal()
        try:
            repo = UserRepository(db)
            users = repo.list_all()
            return [
                UserInDB(
                    id=u.id, username=u.username, role=u.role,
                    full_name=u.full_name or "", is_active=u.is_active,
                    hashed_password=u.hashed_password,
                )
                for u in users
            ]
        finally:
            db.close()

    def get(self, key, default=None):
        return get_user_by_id(key) or default

    def __getitem__(self, key):
        u = get_user_by_id(key)
        if not u:
            raise KeyError(key)
        return u

    def __setitem__(self, key, value):
        # Direct write — should not happen with DB
        pass


_users_db = _UsersDBProxy()
