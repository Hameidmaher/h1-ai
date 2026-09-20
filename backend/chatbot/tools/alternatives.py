"""
Alternative Drugs — البدائل
"""
from __future__ import annotations
from sqlalchemy import text
import structlog

from chatbot.tools.registry import Tool, ToolResult

logger = structlog.get_logger()


# ═══════════════════════════════════════════════════════════
#  Handler — البدائل
# ═══════════════════════════════════════════════════════════
async def find_alternatives_handler(
    drug_name: str,
    context: dict,
) -> ToolResult:
    """
    اقترح بدائل لنفس المادة الفعالة بسعر أرخص.
    """
    from db import SessionLocal

    pharmacy_id = context.get("pharmacy_id")
    session = SessionLocal()

    try:
        # 1. ابحث عن المادة الفعالة للدواء المطلوب
        sql_active = text("""
            SELECT scientific_name, id
            FROM drugs
            WHERE trade_name ILIKE :q OR trade_name_en ILIKE :q
            LIMIT 1
        """)
        row = session.execute(
            sql_active, {"q": f"%{drug_name}%"}
        ).first()

        if not row:
            return ToolResult.ok(
                data={"found": False, "alternatives": []},
                message=f"'{drug_name}' مش موجود",
            )

        active_ingredient = row.scientific_name

        # 2. جيب بدائل بنفس المادة الفعالة
        sql_alts = text("""
            SELECT
                d.trade_name,
                d.trade_name_en,
                d.form,
                d.strength,
                d.price_egp,
                i.selling_price,
                i.quantity
            FROM drugs d
            LEFT JOIN inventory i
                ON i.drug_id = d.id AND i.pharmacy_id = :pharmacy_id
            WHERE d.scientific_name = :sci
              AND d.trade_name NOT ILIKE :q
            ORDER BY COALESCE(i.selling_price, d.price_egp) ASC
            LIMIT 5
        """)

        alts = session.execute(
            sql_alts,
            {
                "pharmacy_id": pharmacy_id,
                "sci": active_ingredient,
                "q": f"%{drug_name}%",
            },
        ).fetchall()

        if not alts:
            return ToolResult.ok(
                data={
                    "found": True,
                    "active": active_ingredient,
                    "alternatives": [],
                },
                message=f"مفيش بدائل متوفرة",
            )

        results = [
            {
                "trade_name": a.trade_name,
                "form": a.form,
                "strength": a.strength,
                "price": float(a.selling_price or a.price_egp or 0),
                "in_stock": (a.quantity or 0) > 0,
            }
            for a in alts
        ]

        return ToolResult.ok(
            data={
                "found": True,
                "active": active_ingredient,
                "alternatives": results,
            },
            message=f"فيه {len(results)} بديل بـ {active_ingredient}",
        )
    finally:
        session.close()


# ═══════════════════════════════════════════════════════════
#  التعريفات
# ═══════════════════════════════════════════════════════════
ALTERNATIVE_TOOLS = [
    Tool(
        name="find_alternatives",
        description=(
            "ابحث عن بدائل لنفس المادة الفعالة، ممكن تكون أرخص. "
            "استخدمها لما العميل يسأل: 'فيه بديل؟' أو 'عايز حاجة أرخص'"
        ),
        parameters={
            "type": "object",
            "properties": {
                "drug_name": {
                    "type": "string",
                    "description": "اسم الدواء الأصلي",
                },
            },
            "required": ["drug_name"],
        },
        handler=find_alternatives_handler,
        requires_context=True,
    ),
]
