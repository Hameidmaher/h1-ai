"""يسمح بـ HEAD و OPTIONS على endpoints الفحص"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp


class HealthMethodsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request, call_next):
        path = request.url.path
        if path in ("/health", "/healthz", "/health/live", "/health/ready"):
            if request.method == "HEAD":
                new_scope = dict(request.scope)
                new_scope["method"] = "GET"
                response = await call_next.__self__(new_scope, request.receive, lambda m: None)
                return Response(status_code=200, headers={"Allow": "GET, HEAD, OPTIONS"})
            if request.method == "OPTIONS":
                return Response(status_code=204, headers={"Allow": "GET, HEAD, OPTIONS"})
        return await call_next(request)
