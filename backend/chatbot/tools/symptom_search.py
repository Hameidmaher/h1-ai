"""
Symptom Search — البحث بالأعراض
يدعم: مرادفات عربية + trigram + بحث في description
"""
from __future__ import annotations
import re
from sqlalchemy import text
import structlog

from chatbot.tools.registry import Tool, ToolResult
from chatbot.data.synonyms import find_symptom_terms

logger = structlog.get_logger()


def _extract_symptom(query: str) -> str:
    """استخرج العرض من السؤال."""
    # شيل "عندي" / "عايز" / "أنا" وغيرهم
    query = re.sub(r'^(عندي|عندى|أنا عندي|عايز|محتاج|عاوز|أحتاج|بقالي)\s+', '', query.strip())
    # شيل "من" و "ال" في الأول
    query = re.sub(r'^(من|ال)', '', query)
    return query.strip()


async def search_by_symptom_handler(
    symptom: str,
    limit: int = 5,
) -> ToolResult:
    """
    ابحث عن أدوية لعلاج عرض معين.
    مثال: "صداع", "كحة", "حرارة"
    """
    from db import SessionLocal

    session = SessionLocal()
    try:
        # استخرج العرض
        symptom_clean = _extract_symptom(symptom)

        # جيب كل مرادفات العرض
        synonyms_list = find_symptom_terms(symptom_clean)
        logger.info(
            "symptom_search.expanded",
            original=symptom_clean,
            synonyms=synonyms_list[:5],
        )

        # ═══ SQL: بحث شامل ═══
        # نبني OR conditions لكل مرادف
        conditions = []
        params = {"limit": limit}

        for i, syn in enumerate(synonyms_list[:10]):  # حد أقصى 10 مرادفات
            key = f"syn_{i}"
            params[key] = f"%{syn}%"
            params[f"syn_exact_{i}"] = syn
            conditions.append(f"""
                (description ILIKE :{key}
                 OR category ILIKE :{key}
                 OR trade_name ILIKE :{key}
                 OR trade_name_en ILIKE :{key})
            """)

        where_clause = " OR ".join(conditions) if conditions else "1=0"

        sql = text(f"""
            SELECT
                id,
                trade_name as name_ar,
                trade_name_en as name_en,
                scientific_name,
                category,
                form,
                strength,
                price_egp as price,
                description,
                prescription_required
            FROM drugs
            WHERE {where_clause}
            ORDER BY
                CASE
                    WHEN trade_name ILIKE :first_syn THEN 1
                    WHEN description ILIKE :first_syn THEN 2
                    ELSE 3
                END,
                LENGTH(COALESCE(trade_name, trade_name_en, '')) ASC
            LIMIT :limit
        """)

        # أضف first_syn
        if synonyms_list:
            params["first_syn"] = f"%{synonyms_list[0]}%"

        rows = session.execute(sql, params).fetchall()

        if not rows:
            return ToolResult.ok(
                data={"drugs": [], "count": 0, "symptom": symptom_clean},
                message=f"مفيش أدوية لـ '{symptom_clean}'",
            )

        drugs = [
            {
                "source": "drug",
                "name_ar": r.name_ar,
                "name_en": r.name_en,
                "scientific_name": r.scientific_name,
                "category": r.category,
                "form": r.form,
                "strength": r.strength,
                "price": float(r.price) if r.price else None,
                "description": r.description,
                "prescription_required": bool(r.prescription_required),
            }
            for r in rows
        ]

        logger.info(
            "symptom_search.success",
            symptom=symptom_clean,
            count=len(drugs),
        )

        return ToolResult.ok(
            data={
                "drugs": drugs,
                "count": len(drugs),
                "symptom": symptom_clean,
                "expanded_terms": synonyms_list[:5],
            },
            message=f"لقيت {len(drugs)} دواء لـ '{symptom_clean}'",
        )
    except Exception as e:
        logger.error("symptom_search.failed", error=str(e)[:200])
        return ToolResult.fail(message=f"خطأ في البحث: {str(e)[:100]}")
    finally:
        session.close()


# ═══════════════════════════════════════════════════════════
#  التعريفات
# ═══════════════════════════════════════════════════════════
SYMPTOM_SEARCH_TOOLS = [
    Tool(
        name="search_by_symptom",
        description=(
            "ابحث عن أدوية لعلاج عرض معين (صداع، كحة، حرارة، إسهال، إلخ). "
            "استخدمها لما العميل يسأل عن دواء لعلاج أعراض أو مرض."
        ),
        parameters={
            "type": "object",
            "properties": {
                "symptom": {
                    "type": "string",
                    "description": "العرض أو المرض (مثل: صداع، كحة، حرارة)",
                },
                "limit": {
                    "type": "integer",
                    "default": 5,
                },
            },
            "required": ["symptom"],
        },
        handler=search_by_symptom_handler,
    ),
]
