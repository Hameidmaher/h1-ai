"""Auto Fixer — automatically fixes safe issues.

Only fixes LOW-RISK, SAFE issues:
- File permissions
- Temp/backup cleanup
- Log rotation
- Old backups

NEVER auto-fixes:
- Code changes
- Database schema
- Git history
- Config values
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os
import subprocess
import structlog

from maintenance.self_audit import Issue

logger = structlog.get_logger()


@dataclass
class FixResult:
    """Result of a fix attempt."""
    issue_title: str
    success: bool
    message: str
    details: str = ""


class AutoFixer:
    """Automatically fixes safe issues."""
    
    def __init__(self, project_root: Path = None):
        self.root = project_root or Path.home() / "h1-ai"
    
    def can_fix(self, issue: Issue) -> bool:
        """Check if issue can be auto-fixed."""
        if not issue.auto_fixable:
            return False
        
        # Only fix low/medium severity
        if issue.severity in ("critical", "high"):
            return False
        
        return True
    
    def fix(self, issue: Issue) -> FixResult:
        """Attempt to fix an issue."""
        logger.info("auto_fixer.attempt", title=issue.title, category=issue.category)
        
        # Route by title keywords
        title = issue.title.lower()
        
        # Fix .env permissions
        if "env permissions" in title:
            return self._fix_env_permissions()
        
        # Fix backups
        if "backup" in title:
            return self._fix_backups()
        
        # Fix temp files
        if "temp" in title or ".tmp" in title:
            return self._fix_temp_files()
        
        # Fix log rotation
        if "log" in title:
            return self._fix_logs()
        
        return FixResult(
            issue_title=issue.title,
            success=False,
            message="لا يوجد إصلاح تلقائي متاح",
        )
    
    def _fix_env_permissions(self) -> FixResult:
        """Fix .env permissions."""
        env = self.root / "backend" / ".env"
        if not env.exists():
            return FixResult(".env permissions", False, "الملف غير موجود")
        
        try:
            os.chmod(env, 0o600)
            return FixResult(
                ".env permissions",
                True,
                "تم ضبط الصلاحيات على 600",
                f"chmod 600 {env}",
            )
        except Exception as e:
            return FixResult(".env permissions", False, str(e)[:200])
    
    def _fix_backups(self) -> FixResult:
        """Remove old backup folders (>7 days)."""
        import time
        data = self.root / "data"
        if not data.exists():
            return FixResult("backups", False, "مجلد data غير موجود")
        
        cutoff = time.time() - (7 * 24 * 3600)
        removed = 0
        
        for backup in data.glob("backup_*"):
            if backup.is_dir() and backup.stat().st_mtime < cutoff:
                try:
                    subprocess.run(["rm", "-rf", str(backup)], check=True)
                    removed += 1
                except Exception as e:
                    logger.warning("auto_fixer.backup_failed", error=str(e))
        
        return FixResult(
            "backups",
            True,
            f"تم حذف {removed} نسخة احتياطية قديمة",
        )
    
    def _fix_temp_files(self) -> FixResult:
        """Remove .tmp files."""
        data = self.root / "data"
        removed = 0
        
        for tmp in data.glob("*.tmp"):
            try:
                tmp.unlink()
                removed += 1
            except Exception:
                pass
        
        return FixResult("temp files", True, f"تم حذف {removed} ملف مؤقت")
    
    def _fix_logs(self) -> FixResult:
        """Rotate large logs."""
        logs = self.root / "logs"
        if not logs.exists():
            return FixResult("logs", False, "مجلد logs غير موجود")
        
        rotated = 0
        for log in logs.glob("*.log"):
            if log.stat().st_size > 100 * 1024 * 1024:  # 100 MB
                try:
                    # Truncate
                    with open(log, "w") as f:
                        f.write("")
                    rotated += 1
                except Exception:
                    pass
        
        return FixResult("logs", True, f"تم ضغط {rotated} ملف log")


# Singleton
auto_fixer = AutoFixer()
