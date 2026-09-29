from typing import Any
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class SessionStore:
    def __init__(self, ttl_minutes: int = 60):
        self._store: dict[str, dict[str, Any]] = {}
        self.ttl = timedelta(minutes=ttl_minutes)

    def get(self, session_id: str) -> dict[str, Any] | None:
        entry = self._store.get(session_id)
        if not entry:
            return None
        if datetime.now() > entry["expires_at"]:
            del self._store[session_id]
            return None
        return entry["data"]

    def set(self, session_id: str, data: dict[str, Any]) -> None:
        self._store[session_id] = {
            "data": data,
            "expires_at": datetime.now() + self.ttl,
        }

    def delete(self, session_id: str) -> None:
        self._store.pop(session_id, None)

    def cleanup_expired(self) -> int:
        now = datetime.now()
        expired = [sid for sid, e in self._store.items()
                   if now > e["expires_at"]]
        for sid in expired:
            del self._store[sid]
        return len(expired)


session_store = SessionStore(ttl_minutes=60)
