"""Index Knowledge Base — يحسب embeddings لكل السجلات"""
import asyncio
import structlog
from sqlalchemy import text

logger = structlog.get_logger()


async def index_knowledge_base(batch_size: int = 20):
    """احسب embeddings للسجلات اللي بدونها."""
    from db import SessionLocal
    from chatbot.rag.retriever import get_rag

    rag = get_rag()
    session = SessionLocal()
    try:
        rows = session.execute(text("""
            SELECT id, title, content
            FROM knowledge_base
            WHERE embedding IS NULL AND is_active = true
            LIMIT :n
        """), {"n": batch_size}).fetchall()

        if not rows:
            print("✅ كل السجلات عندها embeddings")
            return

        print(f"▶ حساب embeddings لـ {len(rows)} سجل...")
        success = 0
        for row in rows:
            text_content = f"{row.title}\n{row.content}"
            emb = await rag.embed(text_content)
            if emb:
                emb_str = "[" + ",".join(str(x) for x in emb) + "]"
                session.execute(text("""
                    UPDATE knowledge_base
                    SET embedding = CAST(:e AS vector)
                    WHERE id = :id
                """), {"e": emb_str, "id": row.id})
                success += 1

        session.commit()
        print(f"✅ تم حساب {success}/{len(rows)} embeddings")
    except Exception as e:
        session.rollback()
        print(f"❌ فشل: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    asyncio.run(index_knowledge_base())
