"""
Inventory Tools — فحص المخزون
"""
from __future__ import annotations
from sqlalchemy import text
import structlog

from chatbot.tools.registry import Tool, ToolResult

logger = structlog.get_logger()


# ═══════════════════════════════════════════════════════════
#  Handler — فحص التوفر
# ═══════════════════════════════════════════════════════════
async def check_availability_handler(
    drug_name: str,
    context: dict,
) -> ToolResult:
    """
    افحص توفر دواء في مخزون صيدلية معينة.
    """
    from db import SessionLocal

    pharmacy_id = context.get("pharmacy_id")
    if not pharmacy_id:
        return ToolResult.fail("مفيش سياق صيدلية")

    session = SessionLocal()
    try:
        sql = text("""
            SELECT
                d.trade_name,
                d.scientific_name,
                d.form,
                d.strength,
                d.price_egp AS catalog_price,
                i.quantity,
                i.reserved,
                (i.quantity - i.reserved) AS available,
                i.selling_price,
                i.expiry_date
            FROM inventory i
            JOIN drugs d ON d.id = i.drug_id
            WHERE i.pharmacy_id = :pharmacy_id
              AND (d.trade_name ILIKE :q OR d.trade_name_en ILIKE :q)
              AND i.quantity > 0
            ORDER BY i.selling_price ASC
            LIMIT 5
        """)

        rows = session.execute(
            sql,
            {"pharmacy_id": pharmacy_id, "q": f"%{drug_name}%"},
        ).fetchall()

        if not rows:
            return ToolResult.ok(
                data={"available": False, "matches": []},
                message=f"'{drug_name}' مش موجود في المخزون حالياً",
            )

        items = [
            {
                "trade_name": r.trade_name,
                "scientific_name": r.scientific_name,
                "form": r.form,
                "strength": r.strength,
                "available": r.available,
                "price": float(r.selling_price) if r.selling_price else None,
                "expiry": str(r.expiry_date) if r.expiry_date else None,
            }
            for r in rows
        ]

        return ToolResult.ok(
            data={"available": True, "matches": items},
            message=f"'{drug_name}' متوفر ({len(items)} نتيجة)",
        )
    finally:
        session.close()


# ═══════════════════════════════════════════════════════════
#  Handler — السعر
# ═══════════════════════════════════════════════════════════
async def check_price_handler(
    drug_name: str,
    context: dict,
) -> ToolResult:
    """اعرف سعر دواء في الصيدلية."""
    from db import SessionLocal

    pharmacy_id = context.get("pharmacy_id")
    session = SessionLocal()

    try:
        sql = text("""
            SELECT
                d.trade_name,
                d.trade_name_en,
                i.selling_price
            FROM inventory i
            JOIN drugs d ON d.id = i.drug_id
            WHERE i.pharmacy_id = :pharmacy_id
              AND (d.trade_name ILIKE :q OR d.trade_name_en ILIKE :q)
            ORDER BY i.selling_price ASC
            LIMIT 3
        """)

        rows = session.execute(
            sql,
            {"pharmacy_id": pharmacy_id, "q": f"%{drug_name}%"},
        ).fetchall()

        if not rows:
            return ToolResult.ok(
                data={"found": False},
                message=f"'{drug_name}' مش موجود في المخزون",
            )

        prices = [
            {
                "trade_name": r.trade_name,
                "price": float(r.selling_price),
            }
            for r in rows
        ]

        return ToolResult.ok(
            data={"found": True, "prices": prices},
            message=f"سعر '{drug_name}': {prices[0]['price']} جنيه",
        )
    finally:
        session.close()


# ═══════════════════════════════════════════════════════════
#  التعريفات
# ═══════════════════════════════════════════════════════════
INVENTORY_TOOLS = [
    Tool(
        name="check_availability",
        description=(
            "افحص توفر دواء معين في مخزون الصيدلية. "
            "استخدمها لما العميل يسأل: 'عندك...؟'"
        ),
        parameters={
            "type": "object",
            "properties": {
                "drug_name": {
                    "type": "string",
                    "description": "اسم الدواء",
                },
            },
            "required": ["drug_name"],
        },
        handler=check_availability_handler,
        requires_context=True,
    ),
    Tool(
        name="check_price",
        description="اعرف سعر دواء في الصيدلية.",
        parameters={
            "type": "object",
            "properties": {
                "drug_name": {
                    "type": "string",
                    "description": "اسم الدواء",
                },
            },
            "required": ["drug_name"],
        },
        handler=check_price_handler,
        requires_context=True,
    ),
]
