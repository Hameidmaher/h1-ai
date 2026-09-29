"""Auto Backup — نسخ احتياطية تلقائية."""
from __future__ import annotations
import shutil
from datetime import datetime
from pathlib import Path
import structlog

logger = structlog.get_logger()


class BackupService:
    def __init__(
        self,
        source_dir: str = "../data",
        backup_dir: str = "../data/.admin/backups",
    ):
        self.source_dir = Path(source_dir)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def backup_file(self, file_name: str) -> bool:
        src = self.source_dir / file_name
        if not src.exists():
            return False
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = Path(file_name).stem
        suffix = Path(file_name).suffix
        dst = self.backup_dir / f"{stem}_{timestamp}{suffix}"
        try:
            shutil.copy2(src, dst)
            logger.info("backup.created", file=file_name, dst=str(dst))
            return True
        except Exception as e:
            logger.error("backup.failed", error=str(e))
            return False

    def backup_all(self) -> list[str]:
        files = [
            "products.csv",
            "drugs.json",
            "symptoms.json",
            "interactions.json",
            "synonyms_ar.json",
            "medical_rules.yaml",
            "emergency_patterns.json",
        ]
        backed = []
        for f in files:
            if self.backup_file(f):
                backed.append(f)
        return backed

    def list_backups(self, file_pattern: str = "") -> list[dict]:
        backups = []
        for p in sorted(self.backup_dir.glob("*")):
            if file_pattern and file_pattern not in p.name:
                continue
            backups.append({
                "name": p.name,
                "size": p.stat().st_size,
                "modified": datetime.fromtimestamp(
                    p.stat().st_mtime
                ).isoformat(),
            })
        return backups[::-1]


backup_service = BackupService()
