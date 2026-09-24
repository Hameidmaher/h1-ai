"""WhatsApp Webhook v2 — full pipeline + admin endpoints."""
from fastapi import APIRouter, HTTPException, Query, Header, Depends, status
from pydantic import BaseModel
from typing import Optional
import structlog
from config import settings

from whatsapp.pipeline import whatsapp_pipeline
from db import SessionLocal
from db.repositories import (
    MessageRepository, ReportRepository,
    TeamRepository,
)

logger = structlog.get_logger()
router = APIRouter(prefix="/webhook/v2", tags=["webhook-v2"])


async def verify_webhook_key(
    x_api_key: str = Header(None, alias="X-API-Key"),
) -> None:
    """Verify webhook API key from header."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-API-Key header",
        )
    if x_api_key != settings.webhook_api_key:
        logger.warning("webhook.invalid_key", key_prefix=x_api_key[:8])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


class IncomingMessage(BaseModel):
    phone: str
    message: str
    name: str = ""
    whatsapp_id: str = ""
    media_type: str = "text"


class PipelineResponse(BaseModel):
    success: bool
    message_id: str
    report_id: Optional[str] = None
    assignment_id: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_to_name: Optional[str] = None
    classification: str
    priority: str
    status: str
    handler: str
    reason: str


@router.post("/incoming", response_model=PipelineResponse)
async def incoming_message(
    req: IncomingMessage,
    _: None = Depends(verify_webhook_key),
):
    """Process incoming WhatsApp message end-to-end."""
    try:
        result = whatsapp_pipeline.process(
            from_phone=req.phone,
            content=req.message,
            from_name=req.name,
            whatsapp_id=req.whatsapp_id or None,
            media_type=req.media_type,
        )
        return PipelineResponse(
            success=result.status in ("assigned", "processed"),
            message_id=result.message_id,
            report_id=result.report_id,
            assignment_id=result.assignment_id,
            assigned_to=result.assigned_to,
            assigned_to_name=result.assigned_to_name,
            classification=result.classification,
            priority=result.priority,
            status=result.status,
            handler=result.handler,
            reason=result.reason,
        )
    except Exception as e:
        logger.error("webhook.error", error=str(e), exc_info=True)
        logger.error("api.unhandled", error=str(e)[:200], exc_info=True)
        raise HTTPException(500, detail="حدث خطأ غير متوقع")


@router.get("/stats")
async def pipeline_stats():
    """Full pipeline statistics."""
    db = SessionLocal()
    try:
        msg_repo = MessageRepository(db)
        report_repo = ReportRepository(db)
        team_repo = TeamRepository(db)
        
        return {
            "messages_24h": msg_repo.stats(24),
            "reports": report_repo.stats(),
            "team": team_repo.stats(),
        }
    finally:
        db.close()


@router.get("/messages")
async def list_messages(
    limit: int = Query(50, ge=1, le=500),
    classification: Optional[str] = None,
):
    """List recent messages."""
    db = SessionLocal()
    try:
        msg_repo = MessageRepository(db)
        messages = msg_repo.list_recent(
            limit=limit,
            classification=classification,
        )
        return {
            "count": len(messages),
            "messages": [m.to_dict() for m in messages],
        }
    finally:
        db.close()


@router.get("/reports")
async def list_reports(
    limit: int = Query(50, ge=1, le=500),
    status: Optional[str] = None,
    priority: Optional[str] = None,
):
    """List recent reports with team member names."""
    db = SessionLocal()
    try:
        report_repo = ReportRepository(db)
        team_repo = TeamRepository(db)
        reports = report_repo.list_recent(
            limit=limit,
            status=status,
            priority=priority,
        )
        
        result = []
        for r in reports:
            data = r.to_dict()
            if r.assigned_to:
                member = team_repo.get_by_id(r.assigned_to)
                if member:
                    data["assigned_to_name"] = member.name_ar or member.name
            result.append(data)
        
        return {"count": len(result), "reports": result}
    finally:
        db.close()


@router.get("/team")
async def list_team():
    """List all team members."""
    db = SessionLocal()
    try:
        team_repo = TeamRepository(db)
        members = team_repo.list_all(active_only=False)
        return {
            "count": len(members),
            "members": [m.to_dict() for m in members],
        }
    finally:
        db.close()


@router.get("/assignments")
async def list_assignments(limit: int = Query(50, ge=1, le=500)):
    """List recent assignments."""
    db = SessionLocal()
    try:
        report_repo = ReportRepository(db)
        team_repo = TeamRepository(db)
        reports = report_repo.list_recent(limit=limit)
        assigned = [r for r in reports if r.assigned_to]
        
        result = []
        for r in assigned:
            data = r.to_dict()
            member = team_repo.get_by_id(r.assigned_to)
            if member:
                data["assigned_to_name"] = member.name_ar or member.name
            result.append(data)
        
        return {"count": len(result), "assignments": result}
    finally:
        db.close()



# ═══════════════════════════════════════════════════════
# TEAM CRUD
# ═══════════════════════════════════════════════════════

from pydantic import BaseModel, Field
from typing import Optional, List


class TeamMemberCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    name_ar: Optional[str] = None
    phone: str = Field(..., min_length=10, max_length=20)
    email: Optional[str] = None
    role: str = "pharmacist"
    specialties: List[str] = []
    shift: str = "morning"
    max_concurrent: int = 10
    languages: List[str] = ["ar"]
    whatsapp_enabled: bool = True


class TeamMemberUpdate(BaseModel):
    name: Optional[str] = None
    name_ar: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    specialties: Optional[List[str]] = None
    shift: Optional[str] = None
    max_concurrent: Optional[int] = None
    languages: Optional[List[str]] = None
    whatsapp_enabled: Optional[bool] = None
    is_active: Optional[bool] = None
    is_available: Optional[bool] = None


@router.post("/team")
async def create_team_member(
    req: TeamMemberCreate,
    _: None = Depends(verify_webhook_key),
):
    """Create new team member."""
    from uuid import uuid4
    db = SessionLocal()
    try:
        team_repo = TeamRepository(db)
        
        # Check phone uniqueness
        existing = team_repo.get_by_phone(req.phone)
        if existing:
            raise HTTPException(400, f"Phone {req.phone} already exists")
        
        member = team_repo.create(
            id=str(uuid4()),
            name=req.name,
            name_ar=req.name_ar,
            phone=req.phone,
            email=req.email,
            role=req.role,
            specialties=req.specialties,
            shift=req.shift,
            max_concurrent=req.max_concurrent,
            languages=req.languages,
            whatsapp_enabled=req.whatsapp_enabled,
        )
        return {"success": True, "member": member.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("team.create.error", error=str(e))
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.put("/team/{member_id}")
async def update_team_member(
    member_id: str,
    req: TeamMemberUpdate,
    _: None = Depends(verify_webhook_key),
):
    """Update team member."""
    db = SessionLocal()
    try:
        team_repo = TeamRepository(db)
        member = team_repo.get_by_id(member_id)
        if not member:
            raise HTTPException(404, "Member not found")
        
        # Apply updates
        updates = req.model_dump(exclude_none=True)
        updated = team_repo.update(member_id, **updates)
        
        return {"success": True, "member": updated.to_dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("team.update.error", error=str(e))
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.delete("/team/{member_id}")
async def delete_team_member(
    member_id: str,
    _: None = Depends(verify_webhook_key),
):
    """Delete team member."""
    db = SessionLocal()
    try:
        team_repo = TeamRepository(db)
        member = team_repo.get_by_id(member_id)
        if not member:
            raise HTTPException(404, "Member not found")
        
        team_repo.delete(member_id)
        return {"success": True, "message": f"Deleted {member.name}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("team.delete.error", error=str(e))
        raise HTTPException(500, str(e))
    finally:
        db.close()


@router.post("/team/{member_id}/toggle")
async def toggle_team_member(
    member_id: str,
    _: None = Depends(verify_webhook_key),
):
    """Toggle member active status."""
    db = SessionLocal()
    try:
        team_repo = TeamRepository(db)
        member = team_repo.get_by_id(member_id)
        if not member:
            raise HTTPException(404, "Member not found")
        
        updated = team_repo.update(member_id, is_active=not member.is_active)
        return {"success": True, "member": updated.to_dict()}
    finally:
        db.close()


# ═══════════════════════════════════════════════════════
# CONSTANTS (for dropdowns)
# ═══════════════════════════════════════════════════════

@router.get("/constants")
async def get_constants():
    """Get available options for dropdowns."""
    return {
        "roles": ["pharmacist", "customer_service", "supervisor", "manager"],
        "shifts": ["morning", "evening", "night", "flexible"],
        "specialties": [
            "prescriptions", "interactions", "inventory",
            "products", "complaints", "escalation",
            "drug_info", "urgent", "suppliers", "general",
            "approval",
        ],
        "languages": ["ar", "en"],
    }
