"""Middleware يضيف Rate Limit headers."""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        limit_info = getattr(request.state, "view_rate_limit", None)
        if limit_info:
            try:
                limit, remaining = limit_info
                response.headers["X-RateLimit-Limit"] = str(limit.amount)
                response.headers["X-RateLimit-Remaining"] = str(
                    max(limit.amount - remaining, 0)
                )
                response.headers["X-RateLimit-Window"] = str(limit.get_expiry())
            except Exception:
                pass
        return response
