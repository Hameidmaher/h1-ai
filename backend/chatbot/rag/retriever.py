"""RAG Retriever — Hybrid: Category → Keyword → FTS → Vector"""
from __future__ import annotations
import structlog
from sqlalchemy import text

logger = structlog.get_logger()

OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"


# ═══════════════════════════════════════════════════════════
#  Category Detection Map
# ═══════════════════════════════════════════════════════════
CATEGORY_MAP = {
    "مواعيد العمل": ["مواعيد", "بتفتحوا", "بتقفلوا", "فاتحين", "ساعات العمل"],
    "التوصيل للمنزل": ["توصيل", "دليفري", "شحن", "توصلوا", "بتوصلوا"],
    "طرق الدفع": ["دفع", "فيزا", "كارت", "كاش", "أونلاين", "ماستركارد"],
    "الروشتة الطبية": ["روشتة", "وصفة"],
    "سياسة الاسترجاع": ["استرجاع", "ترجع", "ترجيح"],
    "الخصوصية": ["خصوصية", "بياناتي"],
    "الصداع": ["صداع"],
    "البرد والرشح": ["برد", "رشح", "زكام"],
    "حساسية": ["حساسية"],
    "التهابات الحلق": ["حلق", "زور"],
}


def detect_category(query: str) -> str | None:
    """يحدد الـ category من السؤال."""
    for category, keywords in CATEGORY_MAP.items():
        if any(kw in query for kw in keywords):
            return category
    return None


class RAGPipeline:
    def __init__(self):
        self.enabled = True

    async def embed(self, text: str) -> list[float] | None:
        import aiohttp
        try:
            async with aiohttp.ClientSession() as s:
                async with s.post(
                    OLLAMA_EMBED_URL,
                    json={"model": EMBED_MODEL, "prompt": text},
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as r:
                    if r.status != 200:
                        return None
                    data = await r.json()
                    return data.get("embedding")
        except Exception as e:
            logger.warning("rag.embed_failed", error=str(e)[:100])
            return None

    async def search(self, query: str, limit: int = 3) -> list[dict]:
        from db import SessionLocal

        session = SessionLocal()
        try:
            # ═══════════════════════════════════════════════
            #  1. Category Detection — الأدق
            # ═══════════════════════════════════════════════
            category = detect_category(query)
            if category:
                # استخدم ILIKE + TRIM للتعامل مع whitespace
                cat_pattern = f"%{category.strip()}%"
                rows = session.execute(text("""
                    SELECT id, category, title, content
                    FROM knowledge_base
                    WHERE is_active = true
                      AND (
                          TRIM(category) ILIKE :cat_pat
                          OR TRIM(title) ILIKE :cat_pat
                      )
                    LIMIT :n
                """), {"cat_pat": cat_pattern, "n": limit}).fetchall()

                if rows:
                    logger.info("rag.category_match", category=category)
                    return [{
                        "id": str(r.id),
                        "category": r.category,
                        "title": r.title,
                        "content": r.content,
                        "similarity": 1.0,
                        "match_type": "category",
                    } for r in rows]

            # ═══════════════════════════════════════════════
            #  2. Keyword Matching — على title + tags
            # ═══════════════════════════════════════════════
            rows = session.execute(text("""
                SELECT id, category, title, content
                FROM knowledge_base
                WHERE is_active = true
                  AND (
                      title ILIKE '%' || :q || '%'
                      OR EXISTS (
                          SELECT 1 FROM unnest(tags) t
                          WHERE :q ILIKE '%' || t || '%'
                             OR t ILIKE '%' || :q || '%'
                      )
                  )
                ORDER BY LENGTH(content) ASC
                LIMIT :n
            """), {"q": query, "n": limit}).fetchall()

            if rows:
                logger.info("rag.keyword_match", count=len(rows))
                return [{
                    "id": str(r.id),
                    "category": r.category,
                    "title": r.title,
                    "content": r.content,
                    "similarity": 0.95,
                    "match_type": "keyword",
                } for r in rows]

            # ═══════════════════════════════════════════════
            #  3. FTS Fallback
            # ═══════════════════════════════════════════════
            rows = session.execute(text("""
                SELECT id, category, title, content,
                       ts_rank(
                           to_tsvector('simple', title || ' ' || content),
                           plainto_tsquery('simple', :q)
                       ) AS rank
                FROM knowledge_base
                WHERE is_active = true
                  AND to_tsvector('simple', title || ' ' || content)
                      @@ plainto_tsquery('simple', :q)
                ORDER BY rank DESC
                LIMIT :n
            """), {"q": query, "n": limit}).fetchall()

            if rows:
                logger.info("rag.fts_match", count=len(rows))
                return [{
                    "id": str(r.id),
                    "category": r.category,
                    "title": r.title,
                    "content": r.content,
                    "similarity": float(r.rank or 0.5),
                    "match_type": "fts",
                } for r in rows]

            # ═══════════════════════════════════════════════
            #  4. Vector Fallback — آخر حل
            # ═══════════════════════════════════════════════
            emb = await self.embed(query)
            if emb:
                emb_str = "[" + ",".join(str(x) for x in emb) + "]"
                try:
                    rows = session.execute(text("""
                        SELECT id, category, title, content,
                               1 - (embedding <=> CAST(:emb AS vector)) AS similarity
                        FROM knowledge_base
                        WHERE is_active = true AND embedding IS NOT NULL
                        ORDER BY embedding <=> CAST(:emb AS vector)
                        LIMIT :n
                    """), {"emb": emb_str, "n": limit}).fetchall()

                    if rows:
                        logger.info("rag.vector_match", count=len(rows))
                        return [{
                            "id": str(r.id),
                            "category": r.category,
                            "title": r.title,
                            "content": r.content,
                            "similarity": float(r.similarity or 0),
                            "match_type": "vector",
                        } for r in rows]
                except Exception as e:
                    logger.warning("rag.vector_failed", error=str(e)[:100])

            return []
        finally:
            session.close()


_rag: RAGPipeline | None = None


def get_rag() -> RAGPipeline:
    global _rag
    if _rag is None:
        _rag = RAGPipeline()
    return _rag
