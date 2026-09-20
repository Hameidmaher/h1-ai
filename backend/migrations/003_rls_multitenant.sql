-- ═══════════════════════════════════════════════════════════
--  Migration 003: Row-Level Security (Multi-tenant)
-- ═══════════════════════════════════════════════════════════

BEGIN;

-- Helper function للحصول على pharmacy_id من session
CREATE OR REPLACE FUNCTION current_pharmacy_id()
RETURNS VARCHAR(36) AS $$
BEGIN
    RETURN current_setting('app.current_pharmacy_id', true);
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

-- Enable RLS
ALTER TABLE chatbot_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE chatbot_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;

-- Policies
DROP POLICY IF EXISTS tenant_isolation ON chatbot_sessions;
CREATE POLICY tenant_isolation ON chatbot_sessions FOR ALL
    USING (current_pharmacy_id() IS NULL OR pharmacy_id = current_pharmacy_id())
    WITH CHECK (current_pharmacy_id() IS NULL OR pharmacy_id = current_pharmacy_id());

DROP POLICY IF EXISTS tenant_isolation ON chatbot_messages;
CREATE POLICY tenant_isolation ON chatbot_messages FOR ALL
    USING (
        current_pharmacy_id() IS NULL
        OR EXISTS (
            SELECT 1 FROM chatbot_sessions cs
            WHERE cs.id = chatbot_messages.session_id
              AND cs.pharmacy_id = current_pharmacy_id()
        )
    );

DROP POLICY IF EXISTS tenant_isolation ON inventory;
CREATE POLICY tenant_isolation ON inventory FOR ALL
    USING (current_pharmacy_id() IS NULL OR pharmacy_id = current_pharmacy_id())
    WITH CHECK (current_pharmacy_id() IS NULL OR pharmacy_id = current_pharmacy_id());

DROP POLICY IF EXISTS tenant_isolation ON orders;
CREATE POLICY tenant_isolation ON orders FOR ALL
    USING (current_pharmacy_id() IS NULL OR pharmacy_id = current_pharmacy_id())
    WITH CHECK (current_pharmacy_id() IS NULL OR pharmacy_id = current_pharmacy_id());

-- Performance index
CREATE INDEX IF NOT EXISTS idx_chatbot_sessions_pharmacy_active
    ON chatbot_sessions (pharmacy_id, updated_at DESC)
    WHERE is_active = true;

COMMIT;

DO $$ BEGIN
    RAISE NOTICE '✅ RLS enabled on 5 tables';
END $$;
