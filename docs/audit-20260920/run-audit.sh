#!/bin/bash
PSQL="PGPASSWORD=h1ai_pass psql -h localhost -U h1ai -d h1ai -P pager=off"

echo "▶ 1. Tables + Sizes + Row counts"
$PSQL -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
    (SELECT COUNT(*) FROM pg_stat_user_tables t2 WHERE t2.relname = tablename) AS _
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

echo "▶ 2. Row counts لكل جدول"
$PSQL -c "
SELECT 
    schemaname,
    relname AS tablename,
    n_live_tup AS live_rows,
    n_dead_tup AS dead_rows,
    ROUND(100.0 * n_dead_tup / NULLIF(n_live_tup + n_dead_tup, 0), 2) AS dead_pct,
    last_vacuum,
    last_autovacuum,
    last_analyze
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;
"

echo "▶ 3. Sequences (لمنع overflow)"
$PSQL -c "
SELECT 
    schemaname,
    sequencename,
    last_value,
    max_value,
    ROUND(100.0 * last_value / max_value, 2) AS usage_pct
FROM pg_sequences
WHERE schemaname = 'public'
ORDER BY usage_pct DESC NULLS LAST;
"

echo "▶ 4. Extensions المثبتة"
$PSQL -c "SELECT extname, extversion FROM pg_extension ORDER BY extname;"

echo "▶ 5. PostgreSQL version + settings"
$PSQL -c "SELECT version();"
$PSQL -c "SELECT name, setting, unit FROM pg_settings WHERE name IN 
('shared_buffers','work_mem','maintenance_work_mem','effective_cache_size',
'random_page_cost','max_connections','wal_level','synchronous_commit');"
