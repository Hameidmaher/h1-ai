"""Middleware يعطي كل طلب request_id فريد."""
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from services.logging_service import set_request_context, clear_request_context
from services.metrics import metrics


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        user = getattr(request.state, "user", None)
        user_id = user.id if user else ""
        set_request_context(request_id=request_id, user_id=user_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            duration_ms = getattr(request.state, "duration_ms", 0)
            metrics.record_request(
                endpoint=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
            )
            return response
        finally:
            clear_request_context()
