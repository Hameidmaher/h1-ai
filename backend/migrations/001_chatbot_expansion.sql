-- ═══════════════════════════════════════════════════════════
--  H1-AI — Migration 001 (FIXED: type compatibility)
-- ═══════════════════════════════════════════════════════════

BEGIN;

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = now(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

-- ═══════════════════════════════════════════════════════════
--  DRUGS (جداول جديدة بـ UUID)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS drugs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trade_name TEXT NOT NULL,
    trade_name_en TEXT,
    scientific_name TEXT NOT NULL,
    barcode TEXT UNIQUE,
    category TEXT,
    form TEXT NOT NULL,
    strength TEXT,
    pack_size INT,
    manufacturer TEXT,
    prescription_required BOOLEAN DEFAULT false,
    price_egp NUMERIC(10,2),
    description TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_drugs_trade ON drugs (LOWER(trade_name));
CREATE INDEX IF NOT EXISTS idx_drugs_sci ON drugs (LOWER(scientific_name));
CREATE INDEX IF NOT EXISTS idx_drugs_fts ON drugs USING gin(to_tsvector('simple', trade_name || ' ' || scientific_name));
DROP TRIGGER IF EXISTS trg_drugs_upd ON drugs;
CREATE TRIGGER trg_drugs_upd BEFORE UPDATE ON drugs FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ═══════════════════════════════════════════════════════════
--  CUSTOMERS (UUID + FK varchar للجداول القديمة)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone TEXT NOT NULL UNIQUE,
    name TEXT,
    email TEXT,
    default_pharmacy_id VARCHAR(36) REFERENCES pharmacies(id) ON DELETE SET NULL,
    whatsapp_opted_in BOOLEAN DEFAULT true,
    loyalty_points INT DEFAULT 0,
    total_spent NUMERIC(12,2) DEFAULT 0,
    last_order_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_cust_phone ON customers (phone);
CREATE INDEX IF NOT EXISTS idx_cust_pharm ON customers (default_pharmacy_id);

-- ═══════════════════════════════════════════════════════════
--  ORDERS (FK: customers=uuid, pharmacies=varchar)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_no TEXT UNIQUE NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    pharmacy_id VARCHAR(36) NOT NULL REFERENCES pharmacies(id) ON DELETE RESTRICT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    type VARCHAR(20) NOT NULL DEFAULT 'pickup',
    subtotal NUMERIC(12,2) DEFAULT 0,
    total NUMERIC(12,2) DEFAULT 0,
    payment_status VARCHAR(20) DEFAULT 'unpaid',
    source VARCHAR(20) DEFAULT 'chatbot',
    chatbot_session_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_orders_cust ON orders (customer_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_orders_pharm ON orders (pharmacy_id, status);

CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    drug_id UUID REFERENCES drugs(id) ON DELETE SET NULL,
    drug_name TEXT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(10,2) NOT NULL,
    line_total NUMERIC(12,2) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_oi_order ON order_items (order_id);
CREATE INDEX IF NOT EXISTS idx_oi_drug ON order_items (drug_id);

-- ═══════════════════════════════════════════════════════════
--  INVENTORY (FK: pharmacy=varchar, drug=uuid)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS inventory (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pharmacy_id VARCHAR(36) NOT NULL REFERENCES pharmacies(id) ON DELETE CASCADE,
    drug_id UUID NOT NULL REFERENCES drugs(id) ON DELETE CASCADE,
    quantity INT NOT NULL DEFAULT 0 CHECK (quantity >= 0),
    reserved INT NOT NULL DEFAULT 0 CHECK (reserved >= 0),
    reorder_level INT DEFAULT 10,
    selling_price NUMERIC(10,2) NOT NULL,
    expiry_date DATE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (pharmacy_id, drug_id)
);
CREATE INDEX IF NOT EXISTS idx_inv_pharm ON inventory (pharmacy_id);
CREATE INDEX IF NOT EXISTS idx_inv_drug ON inventory (drug_id);
CREATE INDEX IF NOT EXISTS idx_inv_low ON inventory (pharmacy_id, quantity) WHERE quantity <= reorder_level;

-- ═══════════════════════════════════════════════════════════
--  CHATBOT (FK: customer=uuid, pharmacy=varchar, assigned_to=varchar)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS chatbot_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
    pharmacy_id VARCHAR(36) REFERENCES pharmacies(id) ON DELETE SET NULL,
    channel VARCHAR(20) NOT NULL,
    channel_user_id TEXT NOT NULL,
    language VARCHAR(5) DEFAULT 'ar',
    state VARCHAR(30) DEFAULT 'greeting',
    context JSONB DEFAULT '{}'::jsonb,
    assigned_to VARCHAR(36) REFERENCES users(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT true,
    total_messages INT DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_cs_cust ON chatbot_sessions (customer_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_cs_channel ON chatbot_sessions (channel, channel_user_id) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_cs_pharm ON chatbot_sessions (pharmacy_id) WHERE is_active = true;

CREATE TABLE IF NOT EXISTS chatbot_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES chatbot_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    intent VARCHAR(50),
    intent_confidence NUMERIC(4,3),
    entities JSONB,
    tool_calls JSONB,
    tool_results JSONB,
    model VARCHAR(50),
    tokens_in INT,
    tokens_out INT,
    latency_ms INT,
    is_error BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_cm_sess ON chatbot_messages (session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_cm_intent ON chatbot_messages (intent) WHERE intent IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_cm_fts ON chatbot_messages USING gin(to_tsvector('simple', content));

-- ═══════════════════════════════════════════════════════════
--  KNOWLEDGE BASE (RAG)
-- ═══════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR(50) NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    language VARCHAR(5) DEFAULT 'ar',
    tags TEXT[],
    embedding vector(1536),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_kb_cat ON knowledge_base (category) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_kb_fts ON knowledge_base USING gin(to_tsvector('simple', title || ' ' || content));

COMMIT;

-- ═══════════════════════════════════════════════════════════
--  Verification
-- ═══════════════════════════════════════════════════════════
DO $$
DECLARE t_count INT;
BEGIN
    SELECT COUNT(*) INTO t_count FROM information_schema.tables
    WHERE table_schema='public' AND table_name IN (
        'drugs','customers','orders','order_items','inventory',
        'chatbot_sessions','chatbot_messages','knowledge_base'
    );
    RAISE NOTICE '✅ Migration 001: % جدول جديد', t_count;
END $$;
