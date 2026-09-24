"""
Drug Search Tools — البحث عن الأدوية (محسّن)
يدعم: عربي + إنجليزي + تطبيع + fuzzy matching
"""
from __future__ import annotations
import re
from sqlalchemy import text
import structlog

from chatbot.tools.registry import Tool, ToolResult

logger = structlog.get_logger()


def _normalize_query(q: str) -> str:
    """تطبيع المدخلات العربية."""
    if not q:
        return q
    q = q.strip()
    # شيل "ال" التعريف من أول الكلمة
    q = re.sub(r'^ال(?=\S{3,})', '', q)
    # شيل التشكيل
    q = re.sub(r'[\u064B-\u065F]', '', q)
    # normalize alef
    q = q.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    # normalize ya
    q = q.replace('ى', 'ي')
    # normalize ta marbuta
    q = q.replace('ة', 'ه')
    return q.strip()


async def search_drug_handler(query: str, limit: int = 5) -> ToolResult:
    """
    ابحث عن دواء بالاسم (عربي/إنجليزي/علمي).
    يستخدم: trigram similarity + ILIKE + تطبيع عربي
    """
    # ═══ حماية: بحث فاضي ═══
    if not query or not query.strip():
        return ToolResult.ok(
            data={"drugs": [], "count": 0, "query": query},
            message="الرجاء إدخال اسم دواء للبحث",
        )

    from db import SessionLocal

    session = SessionLocal()
    try:
        # ═══ تطبيع query ═══
        q_norm = _normalize_query(query)
        like_pattern = f"%{q_norm}%"

        # ═══ SQL: بحث شامل في drugs + products ═══
        sql = text("""
            WITH candidates AS (
                -- من جدول drugs
                SELECT
                    'drug' as source,
                    trade_name as name_ar,
                    trade_name_en as name_en,
                    scientific_name,
                    category,
                    form,
                    strength,
                    price_egp as price,
                    description,
                    prescription_required,
                    GREATEST(
                        similarity(trade_name, :q),
                        similarity(trade_name_en, :q),
                        similarity(COALESCE(scientific_name,''), :q)
                    ) as sim_score
                FROM drugs
                WHERE
                    trade_name % :q
                    OR trade_name_en % :q
                    OR scientific_name % :q
                    OR trade_name ILIKE :like
                    OR trade_name_en ILIKE :like
                    OR scientific_name ILIKE :like
                    OR trade_name ILIKE :like_norm
                    OR trade_name_en ILIKE :like_norm
                    OR scientific_name ILIKE :like_norm

                UNION ALL

                -- من جدول products
                SELECT
                    'product' as source,
                    NULL as name_ar,
                    name as name_en,
                    NULL as scientific_name,
                    category,
                    NULL as form,
                    NULL as strength,
                    price,
                    description,
                    false as prescription_required,
                    similarity(name, :q) as sim_score
                FROM products
                WHERE
                    name % :q
                    OR name ILIKE :like
                    OR name ILIKE :like_norm
            )
            SELECT
                source, name_ar, name_en, scientific_name,
                category, form, strength, price,
                description, prescription_required, sim_score
            FROM candidates
            ORDER BY sim_score DESC, LENGTH(COALESCE(name_ar, name_en, '')) ASC
            LIMIT :limit
        """)

        rows = session.execute(
            sql,
            {
                "q": q_norm,
                "like": f"%{query}%",
                "like_norm": like_pattern,
                "limit": limit,
            },
        ).fetchall()

        if not rows:
            return ToolResult.ok(
                data={"drugs": [], "count": 0, "query": query},
                message=f"مفيش نتائج لـ '{query}'",
            )

        drugs = [
            {
                "source": r.source,
                "name_ar": r.name_ar,
                "name_en": r.name_en,
                "scientific_name": r.scientific_name,
                "category": r.category,
                "form": r.form,
                "strength": r.strength,
                "price": float(r.price) if r.price else None,
                "description": r.description,
                "prescription_required": bool(r.prescription_required),
                "similarity": round(float(r.sim_score or 0), 3),
            }
            for r in rows
        ]

        logger.info(
            "drug_search.success",
            query=query,
            normalized=q_norm,
            count=len(drugs),
            top_match=drugs[0].get("name_ar") or drugs[0].get("name_en"),
        )

        return ToolResult.ok(
            data={"drugs": drugs, "count": len(drugs), "query": query},
            message=f"لقيت {len(drugs)} نتيجة لـ '{query}'",
        )
    except Exception as e:
        logger.error("drug_search.failed", error=str(e)[:200], query=query)
        return ToolResult.fail(message=f"خطأ في البحث: {str(e)[:100]}")
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
                    "description": "اسم الدواء للبحث عنه",
                },
                "limit": {
                    "type": "integer",
                    "description": "عدد النتائج الأقصى",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
        handler=search_drug_handler,
    ),
]
