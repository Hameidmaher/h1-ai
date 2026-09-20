-- ═══════════════════════════════════════════════════════════
--  Seed: Test Pharmacy + Inventory
-- ═══════════════════════════════════════════════════════════

BEGIN;

-- ─── 1. صيدلية تجريبية ─────────────────────────────────
-- افحص لو موجودة
DO $$
DECLARE
    ph_id VARCHAR(36);
BEGIN
    -- شوف لو موجودة صيدلية بالاسم
    SELECT id INTO ph_id FROM pharmacies WHERE name = 'صيدلية النور' LIMIT 1;

    IF ph_id IS NULL THEN
        -- أنشئ صيدلية جديدة
        INSERT INTO pharmacies (
            id, name, phone, address, city, governorate,
            is_active, subscription_status, created_at, updated_at
        ) VALUES (
            gen_random_uuid()::text,
            'صيدلية النور',
            '01001234567',
            'شارع الجمهورية، المعادي',
            'القاهرة',
            'القاهرة',
            true,
            'active',
            now(),
            now()
        )
        RETURNING id INTO ph_id;

        RAISE NOTICE '✅ صيدلية جديدة اتنشأت: %', ph_id;
    ELSE
        RAISE NOTICE 'ℹ️  صيدلية موجودة: %', ph_id;
    END IF;
END $$;

COMMIT;

-- ─── 2. عرض الصيدلية ─────────────────────────────────
SELECT id, name, phone, city, is_active
FROM pharmacies
ORDER BY created_at DESC
LIMIT 3;
