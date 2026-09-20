-- ═══════════════════════════════════════════════════════════
--  Migration 002 — تغيير embedding من 1536 إلى 768
--  السبب: nomic-embed-text بيطلع 768 dim
-- ═══════════════════════════════════════════════════════════

BEGIN;

-- 1. امسح الفهرس لو موجود
DROP INDEX IF EXISTS idx_kb_embedding;

-- 2. احذف العمود القديم
ALTER TABLE knowledge_base DROP COLUMN IF EXISTS embedding;

-- 3. أضف العمود الجديد بـ 768
ALTER TABLE knowledge_base ADD COLUMN embedding vector(768);

-- 4. (اختياري) فهرس HNSW للبحث السريع — نضيفه بعدين لما نكون فيه بيانات كافية
-- CREATE INDEX idx_kb_embedding ON knowledge_base 
--     USING hnsw (embedding vector_cosine_ops);

COMMIT;

DO $$
BEGIN
    RAISE NOTICE '✅ Migration 002: embedding column = vector(768)';
END $$;
