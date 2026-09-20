"""
Drug Search Tools — البحث عن الأدوية
"""
from __future__ import annotations
from sqlalchemy import text
import structlog

from chatbot.tools.registry import Tool, ToolResult

logger = structlog.get_logger()


# ═══════════════════════════════════════════════════════════
#  Handler — البحث عن دواء
# ═══════════════════════════════════════════════════════════
async def search_drug_handler(query: str, limit: int = 5) -> ToolResult:
    """
    ابحث عن دواء بالاسم (عربي/إنجليزي/علمي).
    """
    from db import SessionLocal

    session = SessionLocal()
    try:
        # FTS + ILIKE بحث مرن
        sql = text("""
            SELECT
                id, trade_name, trade_name_en, scientific_name,
                category, form, strength, price_egp, description,
                prescription_required,
                ts_rank(
                    to_tsvector('simple',
                        COALESCE(trade_name,'') || ' ' ||
                        COALESCE(trade_name_en,'') || ' ' ||
                        COALESCE(scientific_name,'')
                    ),
                    plainto_tsquery('simple', :q)
                ) AS rank
            FROM drugs
            WHERE
                trade_name ILIKE :like
                OR trade_name_en ILIKE :like
                OR scientific_name ILIKE :like
                OR to_tsvector('simple',
                        COALESCE(trade_name,'') || ' ' ||
                        COALESCE(trade_name_en,'') || ' ' ||
                        COALESCE(scientific_name,'')
                   ) @@ plainto_tsquery('simple', :q)
            ORDER BY rank DESC NULLS LAST, LENGTH(trade_name) ASC
            LIMIT :limit
        """)

        rows = session.execute(
            sql,
            {"q": query, "like": f"%{query}%", "limit": limit},
        ).fetchall()

        if not rows:
            return ToolResult.ok(
                data={"drugs": [], "count": 0},
                message=f"مفيش نتائج لـ '{query}'",
            )

        drugs = [
            {
                "id": str(r.id),
                "trade_name": r.trade_name,
                "trade_name_en": r.trade_name_en,
                "scientific_name": r.scientific_name,
                "category": r.category,
                "form": r.form,
                "strength": r.strength,
                "price": float(r.price_egp) if r.price_egp else None,
                "description": r.description,
                "prescription_required": r.prescription_required,
            }
            for r in rows
        ]

        return ToolResult.ok(
            data={"drugs": drugs, "count": len(drugs)},
            message=f"لقيت {len(drugs)} دواء لـ '{query}'",
        )
    finally:
        session.close()


# ═══════════════════════════════════════════════════════════
#  التعريفات
# ═══════════════════════════════════════════════════════════
DRUG_SEARCH_TOOLS = [
    Tool(
        name="search_drug",
        description=(
            "ابحث عن دواء في كتالوج الأدوية بالاسم التجاري (عربي أو إنجليزي) "
            "أو الاسم العلمي. استخدمها لما العميل يسأل عن دواء معين."
        ),
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "اسم الدواء (مثال: بنادول، Panadol، Paracetamol)",
                },
                "limit": {
                    "type": "integer",
                    "description": "أقصى عدد نتائج (افتراضي 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
        handler=search_drug_handler,
    ),
]
