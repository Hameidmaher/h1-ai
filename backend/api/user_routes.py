"""User API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user, require_admin
from auth.jwt_handler import hash_password, verify_password
from db import get_db
from db.repositories import UserRepository, AuditRepository
from models.user_schemas import (
    UserResponse, UserUpdate, PasswordChange,
    UserCreateAdmin, UserList,
)
from models.schemas import User
import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/v1/users", tags=["users"])


def _to_response(user) -> UserResponse:
    return UserResponse(**user.to_dict())


# ═══════════════════════════════════════════════════════════
# Current User Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("/me", response_model=UserResponse)
async def get_me(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current user profile."""
    repo = UserRepository(db)
    db_user = repo.get_by_id(user.id)
    if not db_user:
        raise HTTPException(404, "User not found")
    return _to_response(db_user)


@router.put("/me", response_model=UserResponse)
async def update_me(
    req: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current user profile."""
    repo = UserRepository(db)
    updated = repo.update(
        user.id,
        full_name=req.full_name,
        email=req.email,
        phone=req.phone,
    )
    if not updated:
        raise HTTPException(404, "User not found")

    # Audit
    audit = AuditRepository(db)
    audit.log(
        user_id=user.id,
        username=user.username,
        action="UPDATE",
        entity="user",
        entity_id=user.id,
        details={"fields": req.model_dump(exclude_none=True)},
    )

    return _to_response(updated)


@router.post("/change-password")
async def change_password(
    req: PasswordChange,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change current user password."""
    repo = UserRepository(db)
    db_user = repo.get_by_id(user.id)
    if not db_user:
        raise HTTPException(404, "User not found")

    if not verify_password(req.current_password, db_user.hashed_password):
        raise HTTPException(400, "Current password is incorrect")

    repo.update(user.id, hashed_password=hash_password(req.new_password))

    # Audit
    audit = AuditRepository(db)
    audit.log(
        user_id=user.id,
        username=user.username,
        action="PASSWORD_CHANGE",
        entity="user",
        entity_id=user.id,
    )

    return {"success": True, "message": "Password changed successfully"}


# ═══════════════════════════════════════════════════════════
# Admin Endpoints
# ═══════════════════════════════════════════════════════════

@router.get("", response_model=UserList)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: str = None,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all users (admin only)."""
    repo = UserRepository(db)
    skip = (page - 1) * page_size
    users = repo.list_all(skip=skip, limit=page_size, role=role)
    total = repo.count(role=role)

    return UserList(
        items=[_to_response(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get user by ID (admin only)."""
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")
    return _to_response(user)


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    req: UserCreateAdmin,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create new user (admin only)."""
    repo = UserRepository(db)

    if repo.get_by_username(req.username):
        raise HTTPException(400, "Username already exists")
    if req.email and repo.get_by_email(req.email):
        raise HTTPException(400, "Email already exists")
    if req.phone and repo.get_by_phone(req.phone):
        raise HTTPException(400, "Phone already exists")

    user = repo.create(
        username=req.username,
        hashed_password=hash_password(req.password),
        role=req.role,
        full_name=req.full_name,
        email=req.email,
        phone=req.phone,
    )

    # Audit
    audit = AuditRepository(db)
    audit.log(
        user_id=admin.id,
        username=admin.username,
        action="CREATE",
        entity="user",
        entity_id=user.id,
        details={"new_user": req.username, "role": req.role},
    )

    return _to_response(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    req: UserUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update user (admin only)."""
    repo = UserRepository(db)
    updated = repo.update(
        user_id,
        full_name=req.full_name,
        email=req.email,
        phone=req.phone,
    )
    if not updated:
        raise HTTPException(404, "User not found")

    audit = AuditRepository(db)
    audit.log(
        user_id=admin.id,
        username=admin.username,
        action="UPDATE",
        entity="user",
        entity_id=user_id,
        details=req.model_dump(exclude_none=True),
    )

    return _to_response(updated)


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete user (admin only)."""
    repo = UserRepository(db)

    # Prevent self-deletion
    if user_id == admin.id:
        raise HTTPException(400, "Cannot delete yourself")

    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    repo.delete(user_id)

    audit = AuditRepository(db)
    audit.log(
        user_id=admin.id,
        username=admin.username,
        action="DELETE",
        entity="user",
        entity_id=user_id,
        details={"username": user.username},
    )

    return {"success": True}


@router.post("/{user_id}/toggle-active", response_model=UserResponse)
async def toggle_active(
    user_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Toggle user active status (admin only)."""
    repo = UserRepository(db)
    user = repo.get_by_id(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    if user_id == admin.id:
        raise HTTPException(400, "Cannot deactivate yourself")

    updated = repo.update(user_id, is_active=not user.is_active)

    audit = AuditRepository(db)
    audit.log(
        user_id=admin.id,
        username=admin.username,
        action="TOGGLE_ACTIVE",
        entity="user",
        entity_id=user_id,
        details={"new_status": updated.is_active},
    )

    return _to_response(updated)
