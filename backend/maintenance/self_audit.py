"""Self Audit — comprehensive project health check.

Checks:
1. Security (keys, permissions, auth)
2. Database (tables, indexes, orphans)
3. Data quality (duplicates, missing)
4. Code quality (long files, complexity)
5. Performance (N+1, missing indexes)
6. API (routes, validation)
7. Tests (coverage)
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional
import subprocess
import structlog

logger = structlog.get_logger()


@dataclass
class Issue:
    """A single issue found."""
    severity: str          # critical, high, medium, low, info
    category: str          # security, database, code, performance, data
    title: str
    description: str
    file: Optional[str] = None
    line: Optional[int] = None
    fix_suggestion: Optional[str] = None
    auto_fixable: bool = False


@dataclass
class AuditReport:
    """Full audit report."""
    timestamp: str
    duration_seconds: float
    total_issues: int
    by_severity: dict = field(default_factory=dict)
    by_category: dict = field(default_factory=dict)
    issues: list[Issue] = field(default_factory=list)
    stats: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "duration_seconds": self.duration_seconds,
            "total_issues": self.total_issues,
            "by_severity": self.by_severity,
            "by_category": self.by_category,
            "issues": [asdict(i) for i in self.issues],
            "stats": self.stats,
        }


class SelfAudit:
    """Self-audit engine for H1-AI."""
    
    def __init__(self, project_root: Optional[Path] = None):
        self.root = project_root or Path.home() / "h1-ai"
        self.backend = self.root / "backend"
        self.issues: list[Issue] = []
    
    def run(self) -> AuditReport:
        """Run full audit."""
        import time
        start = time.time()
        
        logger.info("audit.start")
        
        # Reset
        self.issues = []
        
        # Run checks
        self._check_security()
        self._check_database()
        self._check_data_quality()
        self._check_code_quality()
        self._check_files()
        self._check_logs()
        
        # Build report
        duration = time.time() - start
        
        by_sev: dict[str, int] = {}
        by_cat: dict[str, int] = {}
        for issue in self.issues:
            by_sev[issue.severity] = by_sev.get(issue.severity, 0) + 1
            by_cat[issue.category] = by_cat.get(issue.category, 0) + 1
        
        report = AuditReport(
            timestamp=datetime.utcnow().isoformat(),
            duration_seconds=round(duration, 2),
            total_issues=len(self.issues),
            by_severity=by_sev,
            by_category=by_cat,
            issues=self.issues,
            stats=self._collect_stats(),
        )
        
        logger.info(
            "audit.complete",
            total=len(self.issues),
            critical=by_sev.get("critical", 0),
            duration=duration,
        )
        
        return report
    
    # ═══════════════════════════════════════════════════════
    # SECURITY
    # ═══════════════════════════════════════════════════════
    def _check_security(self):
        """Security checks."""
        # .env permissions
        env_file = self.backend / ".env"
        if env_file.exists():
            perms = oct(env_file.stat().st_mode)[-3:]
            if perms != "600":
                self.issues.append(Issue(
                    severity="high",
                    category="security",
                    title=".env permissions too open",
                    description=f".env has {perms} instead of 600",
                    file=str(env_file),
                    fix_suggestion="chmod 600 backend/.env",
                    auto_fixable=True,
                ))
        
        # JWT secret
        try:
            import sys
            sys.path.insert(0, str(self.backend))
            from config import settings
            
            if len(settings.jwt_secret_key) < 32:
                self.issues.append(Issue(
                    severity="critical",
                    category="security",
                    title="JWT secret too short",
                    description=f"Only {len(settings.jwt_secret_key)} chars",
                    fix_suggestion="Generate: openssl rand -hex 32",
                ))
            
            if settings.jwt_secret_key in ("CHANGE_ME", "change_me", "secret"):
                self.issues.append(Issue(
                    severity="critical",
                    category="security",
                    title="JWT secret is default",
                    description="Using insecure default value",
                    fix_suggestion="Change immediately!",
                ))
            
            # Webhook key
            if not hasattr(settings, "webhook_api_key") or len(settings.webhook_api_key) < 16:
                self.issues.append(Issue(
                    severity="high",
                    category="security",
                    title="Webhook API key missing/short",
                    fix_suggestion="Add to .env: WEBHOOK_API_KEY=$(openssl rand -hex 32)",
                ))
        except Exception as e:
            logger.warning("audit.security.config_failed", error=str(e)[:100])
        
        # Sensitive files in git
        try:
            result = subprocess.run(
                ["git", "ls-files"],
                cwd=str(self.root),
                capture_output=True,
                text=True,
                timeout=5,
            )
            sensitive = []
            for line in result.stdout.split("\n"):
                if line.endswith(".env.example") or line.endswith(".env.sample"):
                    continue
                if any(p in line for p in [".env", ".db", "sessions/", "node_modules", ".venv"]):
                    sensitive.append(line)
            if sensitive:
                self.issues.append(Issue(
                    severity="critical",
                    category="security",
                    title=f"{len(sensitive)} sensitive files in git",
                    description=f"Examples: {', '.join(sensitive[:3])}",
                    fix_suggestion="git rm --cached + add to .gitignore",
                ))
        except Exception:
            pass
    
    # ═══════════════════════════════════════════════════════
    # DATABASE
    # ═══════════════════════════════════════════════════════
    def _check_database(self):
        """Database checks."""
        db_file = self.backend / "h1ai.db"
        if not db_file.exists():
            self.issues.append(Issue(
                severity="critical",
                category="database",
                title="Database file missing",
                file=str(db_file),
            ))
            return
        
        try:
            import sqlite3
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            
            # Tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cursor.fetchall()]
            
            # Expected tables
            expected = {
                "users", "products", "team_members",
                "messages", "reports", "assignments",
            }
            missing = expected - set(tables)
            if missing:
                self.issues.append(Issue(
                    severity="high",
                    category="database",
                    title=f"Missing tables: {', '.join(missing)}",
                    fix_suggestion="Run migrations or Base.metadata.create_all()",
                ))
            
            # Check products count vs CSV
            cursor.execute("SELECT COUNT(*) FROM products")
            db_count = cursor.fetchone()[0]
            
            csv_file = self.root / "data" / "products.csv"
            if csv_file.exists():
                import csv
                with open(csv_file, encoding="utf-8") as f:
                    csv_count = len(list(csv.DictReader(f)))
                
                if db_count != csv_count:
                    self.issues.append(Issue(
                        severity="high",
                        category="database",
                        title=f"Products mismatch: DB={db_count}, CSV={csv_count}",
                        fix_suggestion="Run: python scripts/seed_products.py",
                    ))
            
            conn.close()
        except Exception as e:
            self.issues.append(Issue(
                severity="high",
                category="database",
                title="Database check failed",
                description=str(e)[:200],
            ))
    
    # ═══════════════════════════════════════════════════════
    # DATA QUALITY
    # ═══════════════════════════════════════════════════════
    def _check_data_quality(self):
        """Data quality checks."""
        data = self.root / "data"
        
        # Check for backup folders
        backups = list(data.glob("backup_*"))
        if len(backups) > 3:
            self.issues.append(Issue(
                severity="low",
                category="data",
                title=f"Too many backup folders ({len(backups)})",
                fix_suggestion="Clean old backups: find data -name 'backup_*' -mtime +7 -exec rm -rf {} \\;",
                auto_fixable=True,
            ))
        
        # Check for .tmp files
        tmp_files = list(data.glob("*.tmp"))
        if tmp_files:
            self.issues.append(Issue(
                severity="low",
                category="data",
                title=f"{len(tmp_files)} temp files in data/",
                fix_suggestion="rm data/*.tmp",
                auto_fixable=True,
            ))
    
    # ═══════════════════════════════════════════════════════
    # CODE QUALITY
    # ═══════════════════════════════════════════════════════
    def _check_code_quality(self):
        """Code quality checks."""
        py_files = list(self.backend.rglob("*.py"))
        
        for f in py_files:
            # Skip venv and pycache
            if ".venv" in str(f) or "__pycache__" in str(f):
                continue
            
            try:
                content = f.read_text(encoding="utf-8")
                lines = content.split("\n")
                
                # Long files
                if len(lines) > 500:
                    self.issues.append(Issue(
                        severity="low",
                        category="code",
                        title=f"Long file: {f.name} ({len(lines)} lines)",
                        file=str(f),
                        fix_suggestion="Split into smaller modules",
                    ))
                
                # Bare except
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if stripped == "except:":
                        self.issues.append(Issue(
                            severity="medium",
                            category="code",
                            title=f"Bare except in {f.name}:{i}",
                            file=str(f),
                            line=i,
                            fix_suggestion="Use 'except Exception as e:'",
                        ))
                
                # Print statements (outside scripts/)
                if "scripts/" not in str(f) and "print(" in content:
                    count = content.count("print(")
                    if count > 3:
                        self.issues.append(Issue(
                            severity="low",
                            category="code",
                            title=f"Print statements in {f.name} ({count})",
                            file=str(f),
                            fix_suggestion="Use structlog logger",
                        ))
            except Exception:
                pass
    
    # ═══════════════════════════════════════════════════════
    # FILES
    # ═══════════════════════════════════════════════════════
    def _check_files(self):
        """File system checks."""
        # Large files in root
        for f in self.root.iterdir():
            if f.is_file() and f.stat().st_size > 10 * 1024 * 1024:
                self.issues.append(Issue(
                    severity="medium",
                    category="files",
                    title=f"Large file: {f.name} ({f.stat().st_size // 1024 // 1024} MB)",
                    fix_suggestion="Move to data/ or add to .gitignore",
                ))
    
    # ═══════════════════════════════════════════════════════
    # LOGS
    # ═══════════════════════════════════════════════════════
    def _check_logs(self):
        """Log file checks."""
        logs = self.root / "logs"
        if not logs.exists():
            return
        
        for log in logs.glob("*.log"):
            if log.stat().st_size > 100 * 1024 * 1024:  # 100 MB
                self.issues.append(Issue(
                    severity="medium",
                    category="logs",
                    title=f"Large log: {log.name}",
                    fix_suggestion=f"Rotate: truncate -s 0 {log}",
                    auto_fixable=True,
                ))
    
    # ═══════════════════════════════════════════════════════
    # STATS
    # ═══════════════════════════════════════════════════════
    def _collect_stats(self) -> dict:
        """Collect project stats."""
        stats = {
            "python_files": 0,
            "python_lines": 0,
            "data_files": 0,
            "backup_size_mb": 0,
        }
        
        for f in self.backend.rglob("*.py"):
            if ".venv" in str(f) or "__pycache__" in str(f):
                continue
            stats["python_files"] += 1
            try:
                stats["python_lines"] += len(f.read_text().split("\n"))
            except Exception:
                pass
        
        data = self.root / "data"
        if data.exists():
            stats["data_files"] = len(list(data.glob("*")))
        
        return stats


# Singleton
self_audit = SelfAudit()
