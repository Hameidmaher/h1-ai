"""Multi-tenant middleware — SECURED"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import text
import re
import structlog

logger = structlog.get_logger()

UUID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE
)


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        pharmacy_id = None

        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            try:
                from auth.jwt_handler import decode_token
                payload = decode_token(token)
                if payload and getattr(payload, 'pharmacy_id', None):
                    pharmacy_id = payload.pharmacy_id
            except Exception as e:
                logger.warning("tenant.jwt_decode_failed", error=str(e)[:100])

        if not pharmacy_id:
            host = request.headers.get("host", "").split(":")[0]
            parts = host.split(".")
            if len(parts) >= 3 and parts[0] not in ("www", "api", "admin", "h", "localhost"):
                subdomain = parts[0]
                if re.match(r'^[a-z0-9-]{1,63}$', subdomain, re.IGNORECASE):
                    pharmacy_id = await self._lookup_by_subdomain(subdomain)

        if pharmacy_id and not UUID_PATTERN.match(pharmacy_id):
            logger.warning("tenant.invalid_pharmacy_id", value=pharmacy_id[:50])
            pharmacy_id = None

        request.state.pharmacy_id = pharmacy_id

        if pharmacy_id:
            await self._set_rls_context(pharmacy_id)

        return await call_next(request)

    async def _lookup_by_subdomain(self, subdomain: str) -> str | None:
        try:
            from db import SessionLocal
            s = SessionLocal()
            r = s.execute(
                text("""
                    SELECT id FROM pharmacies
                    WHERE LOWER(REPLACE(name, ' ', '-')) = LOWER(:sub)
                    LIMIT 1
                """),
                {"sub": subdomain}
            ).first()
            s.close()
            return str(r[0]) if r else None
        except Exception as e:
            logger.warning("tenant.lookup_failed", sub=subdomain, error=str(e)[:100])
            return None

    async def _set_rls_context(self, pharmacy_id: str):
        try:
            from db import engine
            with engine.connect() as conn:
                conn.execute(
                    text("SELECT set_config('app.current_pharmacy_id', :pid, false)"),
                    {"pid": pharmacy_id}
                )
        except Exception as e:
            logger.warning("tenant.rls_set_failed", error=str(e)[:100])
