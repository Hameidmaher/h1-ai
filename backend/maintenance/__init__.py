"""Self-maintenance and audit system."""
from maintenance.self_audit import self_audit, SelfAudit

# Optional modules (import when available)
try:
    from maintenance.ai_analyzer import ai_analyzer, AIAnalyzer
except ImportError:
    ai_analyzer = None
    AIAnalyzer = None

try:
    from maintenance.auto_fixer import auto_fixer, AutoFixer
except ImportError:
    auto_fixer = None
    AutoFixer = None

__all__ = [
    "self_audit", "SelfAudit",
    "ai_analyzer", "AIAnalyzer",
    "auto_fixer", "AutoFixer",
]
