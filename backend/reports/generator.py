"""Report Generator — converts a message into a structured report.

Report types:
- customer_inquiry: customer asking about products/prices
- prescription_review: customer wants prescription review
- interaction_check: customer asking about drug interactions
- supplier_offer: supplier offering products
- complaint: customer complaint
- urgent: emergency/urgent case
- general: general inquiry
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4
import structlog

logger = structlog.get_logger()


# ═══════════════════════════════════════════════════════
# SLA Configuration (minutes)
# ═══════════════════════════════════════════════════════
SLA_MINUTES = {
    "urgent": 5,
    "high": 15,
    "normal": 60,
    "low": 240,
}

# ═══════════════════════════════════════════════════════
# Report Templates (title / summary / category)
# ═══════════════════════════════════════════════════════
REPORT_TEMPLATES = {
    "customer_inquiry": {
        "title_template": "استفسار من عميل — {phone}",
        "summary_template": "عميل يسأل عن: {content_short}",
        "category": "product_inquiry",
        "priority_default": "normal",
        "specialty_required": ["products", "general"],
    },
    "prescription_review": {
        "title_template": "مراجعة وصفة طبية — {phone}",
        "summary_template": "وصفة تحتاج مراجعة: {content_short}",
        "category": "prescription",
        "priority_default": "high",
        "specialty_required": ["prescriptions"],
    },
    "interaction_check": {
        "title_template": "فحص تداخل دوائي — {phone}",
        "summary_template": "فحص تداخلات: {content_short}",
        "category": "interaction",
        "priority_default": "high",
        "specialty_required": ["interactions"],
    },
    "supplier_offer": {
        "title_template": "عرض من مورد — {phone}",
        "summary_template": "مورد يعرض: {content_short}",
        "category": "supplier",
        "priority_default": "low",
        "specialty_required": ["inventory", "suppliers"],
    },
    "complaint": {
        "title_template": "شكوى — {phone}",
        "summary_template": "شكوى: {content_short}",
        "category": "complaint",
        "priority_default": "high",
        "specialty_required": ["complaints", "escalation"],
    },
    "urgent": {
        "title_template": "🚨 حالة عاجلة — {phone}",
        "summary_template": "حالة عاجلة: {content_short}",
        "category": "urgent",
        "priority_default": "urgent",
        "specialty_required": ["urgent", "general"],
    },
    "general": {
        "title_template": "استفسار عام — {phone}",
        "summary_template": "استفسار: {content_short}",
        "category": "general",
        "priority_default": "normal",
        "specialty_required": ["general"],
    },
}


# ═══════════════════════════════════════════════════════
# Classification → Report Type mapping
# ═══════════════════════════════════════════════════════
CLASSIFICATION_TO_REPORT = {
    "customer": "customer_inquiry",
    "supplier": "supplier_offer",
    "urgent": "urgent",
    "spam": None,  # spam = no report
    "unknown": "general",
}


# ═══════════════════════════════════════════════════════
# Content → specific report type (finer detection)
# ═══════════════════════════════════════════════════════
def detect_specific_type(content: str) -> Optional[str]:
    """Detect specific report type from content."""
    content_lower = content.lower()
    
    # Prescription
    for kw in ["وصفة", "روشتة", "prescription", "وصفة طبية"]:
        if kw in content_lower:
            return "prescription_review"
    
    # Interaction
    for kw in ["تداخل", "تفاعل", "interaction", "مع بعض"]:
        if kw in content_lower:
            return "interaction_check"
    
    # Complaint
    for kw in ["شكوى", "زعلان", "سيء", "وحش", "سيئة", "مش راضي", "زفت"]:
        if kw in content_lower:
            return "complaint"
    
    return None


@dataclass
class GeneratedReport:
    """In-memory representation of a report."""
    id: str
    message_id: str
    type: str
    category: str
    priority: str
    title: str
    summary: str
    content: dict
    specialty_required: list[str]
    sla_deadline: datetime
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "message_id": self.message_id,
            "type": self.type,
            "category": self.category,
            "priority": self.priority,
            "title": self.title,
            "summary": self.summary,
            "content": self.content,
            "specialty_required": self.specialty_required,
            "sla_deadline": self.sla_deadline.isoformat(),
            "created_at": self.created_at.isoformat(),
        }


class ReportGenerator:
    """Generates structured reports from messages."""
    
    def generate(
        self,
        message_id: str,
        content: str,
        classification: str = "customer",
        from_phone: str = "",
        from_name: str = "",
        priority_override: Optional[str] = None,
        extra: Optional[dict] = None,
    ) -> Optional[GeneratedReport]:
        """Generate a report from a message.
        
        Returns None if message should not generate a report (e.g., spam).
        """
        # Skip spam
        base_type = CLASSIFICATION_TO_REPORT.get(classification)
        if base_type is None:
            logger.debug("report.skipped", reason="spam", classification=classification)
            return None
        
        # Refine type
        specific = detect_specific_type(content)
        report_type = specific or base_type
        
        # Get template
        template = REPORT_TEMPLATES.get(report_type, REPORT_TEMPLATES["general"])
        
        # Priority
        priority = priority_override or template["priority_default"]
        
        # SLA deadline
        sla_minutes = SLA_MINUTES.get(priority, 60)
        sla_deadline = datetime.utcnow() + timedelta(minutes=sla_minutes)
        
        # Short content for title/summary
        content_short = content[:80] + ("..." if len(content) > 80 else "")
        
        # Title
        title = template["title_template"].format(
            phone=from_phone or "unknown",
            content_short=content_short,
        )
        
        # Summary
        summary = template["summary_template"].format(
            content_short=content_short,
        )
        
        # Structured content
        report_content = {
            "original_message": content,
            "from_phone": from_phone,
            "from_name": from_name,
            "classification": classification,
            "detected_type": report_type,
            "sla_minutes": sla_minutes,
        }
        if extra:
            report_content.update(extra)
        
        report = GeneratedReport(
            id=str(uuid4()),
            message_id=message_id,
            type=report_type,
            category=template["category"],
            priority=priority,
            title=title,
            summary=summary,
            content=report_content,
            specialty_required=list(template["specialty_required"]),
            sla_deadline=sla_deadline,
        )
        
        logger.info(
            "report.generated",
            report_id=report.id,
            type=report_type,
            priority=priority,
            sla_minutes=sla_minutes,
        )
        
        return report


# Singleton
report_generator = ReportGenerator()
