"""Auth Context Middleware — يضبط request.state.user قبل الـ limiter."""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from auth.jwt_handler import decode_token
from auth.dependencies import get_user_by_id
import structlog

logger = structlog.get_logger()


class AuthContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            payload = decode_token(token)
            if payload and payload.type == "access":
                user_db = get_user_by_id(payload.sub)
                if user_db and user_db.is_active:
                    request.state.user = user_db
        return await call_next(request)
