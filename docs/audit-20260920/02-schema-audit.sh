#!/bin/bash
PSQL="PGPASSWORD=h1ai_pass psql -h localhost -U h1ai -d h1ai -P pager=off"

echo "▶ 1. الأعمدة اللي شكلها JSON/CSV (مخالفة 1NF)"
$PSQL -c "
SELECT 
    table_name,
    column_name,
    data_type,
    character_maximum_length
FROM information_schema.columns
WHERE table_schema = 'public'
  AND (column_name LIKE '%_ids' 
       OR column_name LIKE '%list%' 
       OR column_name LIKE '%array%'
       OR column_name LIKE '%csv%')
ORDER BY table_name, column_name;
"

echo "▶ 2. الأعمدة بدون NOT NULL وبدون DEFAULT (خطر NULL)"
$PSQL -c "
SELECT 
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND is_nullable = 'YES'
  AND column_default IS NULL
  AND column_name NOT IN ('id', 'created_at', 'updated_at')
ORDER BY table_name, column_name;
"

echo "▶ 3. الـ Primary Keys (تأكد كل جدول عنده PK)"
$PSQL -c "
SELECT 
    t.table_name,
    COALESCE(pk.constraint_name, '❌ MISSING PK') AS pk
FROM information_schema.tables t
LEFT JOIN (
    SELECT tc.table_name, tc.constraint_name
    FROM information_schema.table_constraints tc
    WHERE tc.constraint_type = 'PRIMARY KEY'
      AND tc.table_schema = 'public'
) pk ON t.table_name = pk.table_name
WHERE t.table_schema = 'public'
  AND t.table_type = 'BASE TABLE'
ORDER BY pk.constraint_name IS NULL DESC, t.table_name;
"

echo "▶ 4. أعمدة مشتركة (created_at/updated_at) — تأكد وجودها"
$PSQL -c "
SELECT 
    t.table_name,
    CASE WHEN c1.column_name IS NULL THEN '❌' ELSE '✅' END AS has_created,
    CASE WHEN c2.column_name IS NULL THEN '❌' ELSE '✅' END AS has_updated
FROM information_schema.tables t
LEFT JOIN information_schema.columns c1 
    ON c1.table_name = t.table_name AND c1.column_name = 'created_at'
LEFT JOIN information_schema.columns c2 
    ON c2.table_name = t.table_name AND c2.column_name = 'updated_at'
WHERE t.table_schema = 'public' AND t.table_type = 'BASE TABLE'
ORDER BY t.table_name;
"

echo "▶ 5. نوع الـ PK (uuid vs serial) — تأكد من consistency"
$PSQL -c "
SELECT 
    tc.table_name,
    c.data_type AS pk_type
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.columns c 
    ON c.table_name = tc.table_name AND c.column_name = kcu.column_name
WHERE tc.constraint_type = 'PRIMARY KEY' 
  AND tc.table_schema = 'public'
ORDER BY c.data_type, tc.table_name;
"
