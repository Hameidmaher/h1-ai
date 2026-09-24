"""Knowledge routes — /v1/knowledge/search, /v1/knowledge/advise."""
from fastapi import APIRouter, Depends

from models.schemas import (
    KnowledgeSearchRequest, KnowledgeAdviseRequest, User,
)
from knowledge.engine import advisory_engine
from auth.dependencies import get_current_user

router = APIRouter(prefix="/v1/knowledge", tags=["knowledge"])


@router.post("/search")
async def knowledge_search(
    req: KnowledgeSearchRequest,
    user: User = Depends(get_current_user),
):
    results = advisory_engine.search(req.query, top_k=req.top_k)
    return {"query": req.query, "count": len(results), "results": results}


@router.post("/advise")
async def knowledge_advise(
    req: KnowledgeAdviseRequest,
    user: User = Depends(get_current_user),
):
    result = advisory_engine.analyze(req.query)
    return result.to_dict()
