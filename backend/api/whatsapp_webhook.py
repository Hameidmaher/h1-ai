"""
WhatsApp Webhook — مع تصنيف العملاء/الموردين
"""
from fastapi import APIRouter
from pydantic import BaseModel
import structlog

from core.orchestrator import orchestrator
from whatsapp.classifier import classifier
from whatsapp.contact_store import contact_store

logger = structlog.get_logger()
router = APIRouter(prefix="/webhook", tags=["webhook"])


class WhatsAppMessage(BaseModel):
    phone: str
    message: str
    timestamp: str = ""


class WhatsAppResponse(BaseModel):
    success: bool = True
    response: str
    handler: str
    classification: str = "unknown"
    confidence: float = 0.0
    should_reply: bool = True
    for_pharmacist: bool = False
    phone: str


@router.post("/whatsapp", response_model=WhatsAppResponse)
async def whatsapp_webhook(req: WhatsAppMessage):
    """
    يستقبل رسالة WhatsApp:
    1. يصنّف الرقم (customer/supplier/spam)
    2. يقرر هل نرد أم لا
    3. يُعيد الرد المناسب
    """
    logger.info(
        "whatsapp.incoming",
        phone=req.phone,
        message=req.message[:80],
    )

    # ═══ Step 1: تحقق من التصنيف المخزّن ═══
    stored_type = contact_store.get_type(req.phone)

    # ═══ Step 2: تصنيف الرسالة ═══
    classification = classifier.classify(req.message)

    # ═══ Step 3: دمج القرار ═══
    # إذا الرقم في القائمة السوداء → تجاهل تماماً
    if stored_type == "blacklist":
        logger.info("whatsapp.blacklisted", phone=req.phone)
        return WhatsAppResponse(
            response="",
            handler="blocked",
            classification="blacklist",
            confidence=1.0,
            should_reply=False,
            for_pharmacist=False,
            phone=req.phone,
        )

    # إذا الرقم مورد معروف → تمرير صامت للصيدلي
    if stored_type == "supplier":
        logger.info("whatsapp.known_supplier", phone=req.phone)
        return WhatsAppResponse(
            response="",
            handler="supplier_passthrough",
            classification="supplier",
            confidence=1.0,
            should_reply=False,
            for_pharmacist=True,
            phone=req.phone,
        )

    # إذا الرسالة spam → تجاهل
    if classification.type == "spam":
        logger.warning("whatsapp.spam", phone=req.phone)
        contact_store.add_blacklist(req.phone, note="auto: spam detected")
        return WhatsAppResponse(
            response="",
            handler="spam_blocked",
            classification="spam",
            confidence=classification.confidence,
            should_reply=False,
            for_pharmacist=False,
            phone=req.phone,
        )

    # إذا الرسالة طوارئ → رد فوري
    if classification.type == "urgent":
        logger.warning("whatsapp.urgent", phone=req.phone)
        result = orchestrator.handle(req.message, user_role="customer")
        return WhatsAppResponse(
            response=result.response.text,
            handler="urgent",
            classification="urgent",
            confidence=1.0,
            should_reply=True,
            for_pharmacist=True,  # إشعار للصيدلي أيضاً
            phone=req.phone,
        )

    # إذا الرقم مورد محتمل → تمرير للصيدلي (بدون رد)
    if classification.type == "supplier":
        logger.info(
            "whatsapp.supplier_detected",
            phone=req.phone,
            matches=classification.matched_supplier[:5],
            score=classification.supplier_score,
        )
        # إضافة تلقائية للموردين (اختياري)
        if classification.confidence > 0.6:
            contact_store.add_supplier(
                req.phone,
                name=f"auto ({classification.matched_supplier[0] if classification.matched_supplier else 'unknown'})",
            )
        return WhatsAppResponse(
            response="",
            handler="supplier_passthrough",
            classification="supplier",
            confidence=classification.confidence,
            should_reply=False,
            for_pharmacist=True,
            phone=req.phone,
        )

    # إذا عميل واضح → رد تلقائي
    if classification.type == "customer":
        logger.info(
            "whatsapp.customer_reply",
            phone=req.phone,
            score=classification.customer_score,
        )
        try:
            result = orchestrator.handle(req.message, user_role="customer")
            return WhatsAppResponse(
                response=result.response.text,
                handler=result.handler,
                classification="customer",
                confidence=classification.confidence,
                should_reply=True,
                for_pharmacist=False,
                phone=req.phone,
            )
        except Exception as e:
            logger.error("whatsapp.error", error=str(e), phone=req.phone)
            return WhatsAppResponse(
                response="عذراً، حدث خطأ مؤقت. حاول تاني.",
                handler="error",
                classification="customer",
                confidence=0.0,
                should_reply=True,
                for_pharmacist=False,
                phone=req.phone,
            )

    # ═══ غامض → تمرير للصيدلي ═══
    logger.info(
        "whatsapp.unknown",
        phone=req.phone,
        supplier_score=classification.supplier_score,
        customer_score=classification.customer_score,
    )
    return WhatsAppResponse(
        response="",
        handler="unknown_passthrough",
        classification="unknown",
        confidence=0.0,
        should_reply=False,
        for_pharmacist=True,
        phone=req.phone,
    )


# ═══════════════════════════════════════════════════════════
# Admin Endpoints لإدارة القوائم
# ═══════════════════════════════════════════════════════════

class ContactRequest(BaseModel):
    phone: str
    name: str = ""
    note: str = ""


@router.get("/contacts")
async def list_contacts(contact_type: str = None):
    """يعيد قائمة الأرقام."""
    return {
        "contacts": contact_store.list_all(contact_type),
        "stats": contact_store.get_stats(),
    }


@router.post("/contacts/customer")
async def add_customer(req: ContactRequest):
    """إضافة عميل."""
    contact_store.add_customer(req.phone, req.name)
    return {"success": True}


@router.post("/contacts/supplier")
async def add_supplier(req: ContactRequest):
    """إضافة مورد."""
    contact_store.add_supplier(req.phone, req.name)
    return {"success": True}


@router.post("/contacts/blacklist")
async def add_blacklist(req: ContactRequest):
    """إضافة رقم للقائمة السوداء."""
    contact_store.add_blacklist(req.phone, req.note)
    return {"success": True}


@router.delete("/contacts/{phone}")
async def remove_contact(phone: str):
    """حذف رقم من القائمة."""
    if contact_store.remove(phone):
        return {"success": True}
    return {"success": False, "error": "not_found"}


@router.post("/test-classify")
async def test_classify(req: ContactRequest):
    """اختبار تصنيف رسالة (dev tool)."""
    classification = classifier.classify(req.note)  # note = text
    return {
        "type": classification.type,
        "confidence": classification.confidence,
        "supplier_score": classification.supplier_score,
        "customer_score": classification.customer_score,
        "matched_supplier": classification.matched_supplier,
        "matched_customer": classification.matched_customer,
        "reason": classification.reason,
    }
