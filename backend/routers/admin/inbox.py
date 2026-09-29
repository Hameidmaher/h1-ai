"""Admin Inbox routes — /v1/admin/inbox/*."""
from fastapi import APIRouter, Depends, HTTPException, Query

from models.schemas import User
from auth.dependencies import require_admin
from services.inbox_service import inbox_service
from pydantic import BaseModel, Field

router = APIRouter(prefix="/v1/admin/inbox", tags=["admin-inbox"])


# ═══════════════════════════════════════════════════════════
#  Models
# ═══════════════════════════════════════════════════════════
class ReplyRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)


class AssignRequest(BaseModel):
    user_id: str
    user_name: str


class StatusRequest(BaseModel):
    status: str = Field(..., pattern="^(open|assigned|pending|closed|archived)$")


# ═══════════════════════════════════════════════════════════
#  Endpoints
# ═══════════════════════════════════════════════════════════
@router.get("/conversations")
async def list_conversations(
    status: str = Query(None, pattern="^(open|assigned|pending|closed|archived)$"),
    assigned_to: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: User = Depends(require_admin),
):
    """List all conversations (admin only)."""
    convs = inbox_service.get_conversations(
        status=status, assigned_to=assigned_to, limit=limit, offset=offset
    )
    return {"conversations": convs, "count": len(convs)}


@router.get("/conversations/{conv_id}")
async def get_conversation(
    conv_id: str,
    user: User = Depends(require_admin),
):
    """Get one conversation with all messages."""
    conv = inbox_service.get_conversation(conv_id)
    if not conv:
        raise HTTPException(404, "Conversation not found")
    return conv


@router.post("/conversations/{conv_id}/reply")
async def reply_to_conversation(
    conv_id: str,
    req: ReplyRequest,
    user: User = Depends(require_admin),
):
    """Reply to a conversation."""
    try:
        result = await inbox_service.reply(
            conv_id=conv_id,
            content=req.content,
            sender_id=user.id,
            sender_name=user.full_name or user.username,
        )
        return result
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.put("/conversations/{conv_id}/assign")
async def assign_conversation(
    conv_id: str,
    req: AssignRequest,
    user: User = Depends(require_admin),
):
    """Assign conversation to a team member."""
    result = await inbox_service.assign(
        conv_id=conv_id,
        user_id=req.user_id,
        user_name=req.user_name,
    )
    if not result.get("success"):
        raise HTTPException(404, "Conversation not found")
    return result


@router.put("/conversations/{conv_id}/status")
async def update_conversation_status(
    conv_id: str,
    req: StatusRequest,
    user: User = Depends(require_admin),
):
    """Update conversation status."""
    result = await inbox_service.update_status(conv_id, req.status)
    if not result.get("success"):
        raise HTTPException(404, "Conversation not found")
    return result


@router.get("/stats")
async def inbox_stats(user: User = Depends(require_admin)):
    """Inbox statistics."""
    return inbox_service.stats()
