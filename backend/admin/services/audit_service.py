"""Audit Log — يسجّل كل تعديل."""
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
import structlog

logger = structlog.get_logger()


class AuditService:
    def __init__(self, log_path: str = "../data/.admin/audit.log"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        user: str,
        action: str,
        entity: str,
        entity_id: str = "",
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user": user,
            "action": action,
            "entity": entity,
            "entity_id": entity_id,
            "details": details or {},
        }
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error("audit.log_failed", error=str(e))

    def read_recent(self, limit: int = 100) -> list[dict]:
        if not self.log_path.exists():
            return []
        entries = []
        with open(self.log_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except Exception:
                        continue
        return entries[-limit:][::-1]


audit_service = AuditService()
