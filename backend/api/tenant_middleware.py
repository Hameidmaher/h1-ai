"""Multi-tenant middleware — يضبط pharmacy_id."""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import text
import structlog

logger = structlog.get_logger()


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        pharmacy_id = None

        # من header
        pharmacy_id = request.headers.get("X-Pharmacy-ID")

        # من subdomain
        if not pharmacy_id:
            host = request.headers.get("host", "")
            if "." in host and host not in ("localhost", "127.0.0.1"):
                subdomain = host.split(".")[0]
                if subdomain and subdomain not in ("www", "api", "admin", "h"):
                    pharmacy_id = await self._lookup_by_subdomain(subdomain)

        request.state.pharmacy_id = pharmacy_id

        if pharmacy_id:
            await self._set_rls_context(pharmacy_id)

        response = await call_next(request)
        return response

    async def _lookup_by_subdomain(self, subdomain: str) -> str | None:
        try:
            from db import SessionLocal
            s = SessionLocal()
            r = s.execute(text("""
                SELECT id FROM pharmacies
                WHERE LOWER(REPLACE(name, ' ', '-')) = LOWER(:sub)
                LIMIT 1
            """), {"sub": subdomain}).first()
            s.close()
            return str(r[0]) if r else None
        except Exception as e:
            logger.warning("tenant.lookup_failed", sub=subdomain, error=str(e)[:100])
            return None

    async def _set_rls_context(self, pharmacy_id: str):
        try:
            from db import engine
            with engine.connect() as conn:
                conn.execute(text(f"SET app.current_pharmacy_id = '{pharmacy_id}'"))
        except Exception as e:
            logger.warning("tenant.rls_set_failed", error=str(e)[:100])
