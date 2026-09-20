#!/bin/bash
PSQL="PGPASSWORD=h1ai_pass psql -h localhost -U h1ai -d h1ai -P pager=off"

echo "▶ 1. Indexes مش مستخدمة إطلاقاً (Dead Weight)"
$PSQL -c "
SELECT 
    schemaname,
    relname AS tablename,
    indexrelname AS indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) AS index_size,
    idx_scan AS times_used
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND indexrelname NOT LIKE '%_pkey'
ORDER BY pg_relation_size(indexrelid) DESC;
"

echo ""
echo "▶ 2. Indexes مكررة أو متقاطعة (Redundant)"
$PSQL -c "
SELECT 
    indrelid::regclass AS table_name,
    array_agg(indexrelid::regclass) AS duplicate_indexes
FROM pg_index
GROUP BY indrelid, indkey
HAVING COUNT(*) > 1;
"

echo ""
echo "▶ 3. جداول كبيرة بدون index على FK"
$PSQL -c "
SELECT 
    c.conrelid::regclass AS table_name,
    a.attname AS column_name
FROM pg_constraint c
JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = ANY(c.conkey)
LEFT JOIN pg_index i ON i.indrelid = c.conrelid AND a.attnum = ANY(i.indkey)
WHERE c.contype = 'f' AND i.indexrelid IS NULL
ORDER BY c.conrelid::regclass::text;
"

echo ""
echo "▶ 4. Index Bloat (indexes متضخمة)"
$PSQL -c "
SELECT 
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) AS size,
    idx_scan
FROM pg_stat_user_indexes
ORDER BY pg_relation_size(indexname::regclass) DESC
LIMIT 15;
"

echo ""
echo "▶ 5. Table Bloat (جداول متضخمة)"
$PSQL -c "
SELECT 
    schemaname,
    tablename,
    n_live_tup AS live,
    n_dead_tup AS dead,
    ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_pct,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_stat_user_tables
WHERE n_dead_tup > 100
ORDER BY n_dead_tup DESC;
"

echo ""
echo "▶ 6. Slow Queries (لو pg_stat_statements مفعل)"
$PSQL -c "
SELECT 
    LEFT(query, 80) AS query,
    calls,
    ROUND(total_exec_time::numeric, 2) AS total_ms,
    ROUND(mean_exec_time::numeric, 2) AS avg_ms,
    ROUND(100.0 * shared_blks_hit / NULLIF(shared_blks_hit + shared_blks_read, 0), 2) AS cache_hit_pct
FROM pg_stat_statements
WHERE query NOT LIKE '%pg_stat%'
ORDER BY mean_exec_time DESC
LIMIT 10;
" 2>/dev/null || echo "  ℹ️  pg_stat_statements مش مفعل — يُنصح بتفعيله"

echo ""
echo "▶ 7. عدد الـ Connections الحالي"
$PSQL -c "
SELECT 
    state,
    COUNT(*) AS count
FROM pg_stat_activity
WHERE datname = 'h1ai'
GROUP BY state;
"

echo ""
echo "▶ 8. Long-running queries (> 1 دقيقة)"
$PSQL -c "
SELECT 
    pid,
    now() - query_start AS duration,
    state,
    LEFT(query, 60) AS query
FROM pg_stat_activity
WHERE datname = 'h1ai'
  AND state != 'idle'
  AND now() - query_start > interval '1 minute'
ORDER BY duration DESC;
"
