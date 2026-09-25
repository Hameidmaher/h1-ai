"""WhatsApp Pipeline — end-to-end message processing.

Flow:
1. Receive incoming message
2. Classify (customer/supplier/spam/urgent)
3. Generate report
4. Assign to team member
5. Create assignment record
6. Send notification (WhatsApp/dashboard)
7. Track SLA

Uses classifier_v2 for better accuracy.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4
from typing import Optional
import structlog

from db import SessionLocal
from db.repositories import (
    MessageRepository, ReportRepository,
    TeamRepository, AssignmentRepository,
)
from whatsapp.classifier_v2 import classifier_v2
from whatsapp.contact_store import contact_store
from reports.generator import report_generator
from reports.distributor import team_distributor

from services.inbox_service import inbox_service

logger = structlog.get_logger()


@dataclass
class PipelineResult:
    """Result of processing a message through the pipeline."""
    message_id: str
    report_id: Optional[str]
    assignment_id: Optional[str]
    assigned_to: Optional[str]
    assigned_to_name: Optional[str]
    classification: str
    priority: str
    status: str
    handler: str
    reason: str
    chatbot_response: Optional[str] = None


class WhatsAppPipeline:
    """Processes WhatsApp messages end-to-end."""
    
    def process(
        self,
        from_phone: str,
        content: str,
        from_name: str = "",
        whatsapp_id: Optional[str] = None,
        media_type: str = "text",
    ) -> PipelineResult:
        """Main entry point — process a WhatsApp message."""
        logger.info(
            "pipeline.start",
            from_phone=from_phone,
            content_len=len(content),
        )
        
        db = SessionLocal()
        try:
            msg_repo = MessageRepository(db)
            report_repo = ReportRepository(db)
            team_repo = TeamRepository(db)
            asgn_repo = AssignmentRepository(db)
            
            # ─── Step 1: Create Message record ───
            message_id = str(uuid4())
            msg = msg_repo.create(
                id=message_id,
                whatsapp_id=whatsapp_id,
                from_phone=from_phone,
                from_name=from_name,
                content=content,
                media_type=media_type,
                direction="inbound",
            )
            
            # ─── Step 2: Check stored contact type ───
            stored_type = contact_store.get_type(from_phone)
            
            # Blacklist → ignore
            if stored_type == "blacklist":
                msg_repo.mark_processed(message_id, handler="blocked")
                # ─── Inbox update ───
                try:
                    inbox_service.create_or_update_from_message(
                        phone=from_phone,
                        content=content,
                        direction="inbound",
                        contact_name=from_name,
                        classification="blacklist",
                        priority="none",
                    )
                except Exception as _ie:
                    logger.warning("pipeline.inbox_failed", error=str(_ie)[:100])
                logger.info("pipeline.blocked", phone=from_phone)
                return PipelineResult(
                    message_id=message_id,
                    report_id=None,
                    assignment_id=None,
                    assigned_to=None,
                    assigned_to_name=None,
                    classification="blacklist",
                    priority="none",
                    status="blocked",
                    handler="blocked",
                    reason="phone is blacklisted",
                )
            
            # ─── Step 3: Classify message (using V2!) ───
            classification = classifier_v2.classify(content)
            cls_type = classification.type
            cls_confidence = classification.confidence
            
            # Override: if stored as supplier, force supplier
            if stored_type == "supplier":
                cls_type = "supplier"
            
            logger.info(
                "pipeline.classified",
                type=cls_type,
                confidence=cls_confidence,
                reason=classification.reason,
            )
            
            # Update message classification
            msg.classification = cls_type
            msg.priority = self._determine_priority(cls_type, content)
            db.commit()
            
            # ─── Step 4: Handle spam ───
            if cls_type == "spam":
                contact_store.add_blacklist(from_phone, note="auto: spam detected")
                msg_repo.mark_processed(message_id, handler="spam_blocked")
                # ─── Inbox update ───
                try:
                    inbox_service.create_or_update_from_message(
                        phone=from_phone,
                        content=content,
                        direction="inbound",
                        contact_name=from_name,
                        classification="spam",
                        priority="none",
                    )
                except Exception as _ie:
                    logger.warning("pipeline.inbox_failed", error=str(_ie)[:100])
                logger.warning("pipeline.spam", phone=from_phone)
                return PipelineResult(
                    message_id=message_id,
                    report_id=None,
                    assignment_id=None,
                    assigned_to=None,
                    assigned_to_name=None,
                    classification="spam",
                    priority="none",
                    status="blocked",
                    handler="spam_blocked",
                    reason="classified as spam",
                )
            
            # ─── Step 5: Generate report ───
            report = report_generator.generate(
                message_id=message_id,
                content=content,
                classification=cls_type,
                from_phone=from_phone,
                from_name=from_name,
                priority_override=msg.priority,
            )
            
            if not report:
                msg_repo.mark_processed(message_id, handler="no_report")
                try:
                    inbox_service.create_or_update_from_message(
                        phone=from_phone,
                        content=content,
                        direction="inbound",
                        contact_name=from_name,
                        classification=cls_type,
                        priority=msg.priority,
                    )
                except Exception as _ie:
                    logger.warning("pipeline.inbox_failed", error=str(_ie)[:100])
                return PipelineResult(
                    message_id=message_id,
                    report_id=None,
                    assignment_id=None,
                    assigned_to=None,
                    assigned_to_name=None,
                    classification=cls_type,
                    priority=msg.priority,
                    status="processed",
                    handler="no_report",
                    reason="no report template",
                )
            
            # Save report to DB
            report_db = report_repo.create(
                id=report.id,
                message_id=message_id,
                type=report.type,
                category=report.category,
                priority=report.priority,
                title=report.title,
                summary=report.summary,
                content=report.content,
                status="pending",
                sla_deadline=report.sla_deadline,
            )
            
            # ─── Step 6: Distribute to team ───
            distribution = team_distributor.distribute(
                team_repo=team_repo,
                report_id=report.id,
                specialty_required=report.specialty_required,
                priority=report.priority,
                language="ar",
            )
            
            if not distribution.success:
                logger.warning(
                    "pipeline.no_team_member",
                    report_id=report.id,
                    reason=distribution.reason,
                )
                msg_repo.mark_processed(message_id, handler="unassigned")
                try:
                    inbox_service.create_or_update_from_message(
                        phone=from_phone,
                        content=content,
                        direction="inbound",
                        contact_name=from_name,
                        classification=cls_type,
                        priority=report.priority,
                    )
                except Exception as _ie:
                    logger.warning("pipeline.inbox_failed", error=str(_ie)[:100])
                return PipelineResult(
                    message_id=message_id,
                    report_id=report.id,
                    assignment_id=None,
                    assigned_to=None,
                    assigned_to_name=None,
                    classification=cls_type,
                    priority=report.priority,
                    status="pending_assignment",
                    handler="unassigned",
                    reason=distribution.reason,
                )
            
            # ─── Step 7: Create assignment ───
            assignment_id = str(uuid4())
            assignment = asgn_repo.create(
                id=assignment_id,
                report_id=report.id,
                team_member_id=distribution.member_id,
                status="assigned",
                sla_deadline=report.sla_deadline,
                priority_score=self._priority_score(report.priority),
            )
            
            # Update report with assignment
            report_repo.assign(report.id, distribution.member_id)
            
            # Increment member load
            team_repo.increment_load(distribution.member_id)
            
            # ─── Step 8: Mark message processed ───
            msg_repo.mark_processed(message_id, handler="reported")

            # ─── Step 9: Update inbox conversation ───
            try:
                inbox_service.create_or_update_from_message(
                    phone=from_phone,
                    content=content,
                    direction="inbound",
                    contact_name=from_name,
                    classification=cls_type,
                    priority=report.priority,
                )
            except Exception as _ie:
                logger.warning("pipeline.inbox_failed", error=str(_ie)[:100])
            
            logger.info(
                "pipeline.complete",
                message_id=message_id,
                report_id=report.id,
                assigned_to=distribution.member_name,
                priority=report.priority,
            )
            
            return PipelineResult(
                message_id=message_id,
                report_id=report.id,
                assignment_id=assignment_id,
                assigned_to=distribution.member_id,
                assigned_to_name=distribution.member_name,
                classification=cls_type,
                priority=report.priority,
                status="assigned",
                handler="reported",
                reason=f"assigned via {distribution.strategy}",
            )
        
        except Exception as e:
            logger.error("pipeline.error", error=str(e), exc_info=True)
            raise
        
        finally:
            db.close()
    
    def _determine_priority(self, classification: str, content: str) -> str:
        """Determine priority based on classification and content."""
        if classification == "urgent":
            return "urgent"
        
        content_lower = content.lower()
        
        # High priority signals
        for kw in ["عاجل", "طارئ", "شكوى", "مشكلة", "urgent", "emergency"]:
            if kw in content_lower:
                return "high"
        
        # Prescription always high
        for kw in ["روشتة", "وصفة", "prescription"]:
            if kw in content_lower:
                return "high"
        
        # Supplier low
        if classification == "supplier":
            return "low"
        
        return "normal"
    
    def _priority_score(self, priority: str) -> int:
        """Convert priority to numeric score."""
        return {
            "urgent": 100,
            "high": 50,
            "normal": 20,
            "low": 5,
        }.get(priority, 10)


# Singleton
whatsapp_pipeline = WhatsAppPipeline()
