"""RAG Retriever — بحث في knowledge_base بـ embeddings"""
from __future__ import annotations
import structlog
from sqlalchemy import text

logger = structlog.get_logger()

OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"  # سنثبته


class RAGPipeline:
    def __init__(self):
        self.enabled = True

    async def embed(self, text: str) -> list[float] | None:
        """توليد embedding للنص."""
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

    async def search(
        self,
        query: str,
        limit: int = 3,
        category: str | None = None,
    ) -> list[dict]:
        """ابحث في knowledge_base."""
        from db import SessionLocal

        # 1. جرّب embeddings
        emb = await self.embed(query)
        session = SessionLocal()
        try:
            if emb:
                # بحث بالـ vector similarity
                emb_str = "[" + ",".join(str(x) for x in emb) + "]"
                sql = text("""
                    SELECT id, category, title, content,
                           1 - (embedding <=> CAST(:emb AS vector)) AS similarity
                    FROM knowledge_base
                    WHERE is_active = true
                      AND embedding IS NOT NULL
                      AND (:cat IS NULL OR category = :cat)
                    ORDER BY embedding <=> CAST(:emb AS vector)
                    LIMIT :n
                """)
                try:
                    rows = session.execute(sql, {
                        "emb": emb_str, "cat": category, "n": limit
                    }).fetchall()
                    if rows:
                        return [
                            {"id": str(r.id), "category": r.category, "title": r.title,
                             "content": r.content, "similarity": float(r.similarity or 0)}
                            for r in rows
                        ]
                except Exception as e:
                    logger.warning("rag.vector_search_failed", error=str(e)[:100])

            # 2. Fallback: FTS
            sql = text("""
                SELECT id, category, title, content,
                       ts_rank(to_tsvector('simple', title || ' ' || content),
                               plainto_tsquery('simple', :q)) AS similarity
                FROM knowledge_base
                WHERE is_active = true
                  AND (:cat IS NULL OR category = :cat)
                  AND to_tsvector('simple', title || ' ' || content)
                      @@ plainto_tsquery('simple', :q)
                ORDER BY similarity DESC
                LIMIT :n
            """)
            rows = session.execute(sql, {"q": query, "cat": category, "n": limit}).fetchall()
            return [
                {"id": str(r.id), "category": r.category, "title": r.title,
                 "content": r.content, "similarity": float(r.similarity or 0)}
                for r in rows
            ]
        finally:
            session.close()


_rag: RAGPipeline | None = None

def get_rag() -> RAGPipeline:
    global _rag
    if _rag is None:
        _rag = RAGPipeline()
    return _rag
