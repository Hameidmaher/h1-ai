"""Middleware لقياس زمن الاستجابة."""
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger()


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        request.state.duration_ms = duration_ms
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        if duration_ms > 1000:
            logger.warning(
                "slow_request",
                path=request.url.path,
                method=request.method,
                duration_ms=round(duration_ms, 2),
            )
        return response
