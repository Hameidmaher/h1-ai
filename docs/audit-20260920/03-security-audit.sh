#!/bin/bash
echo "═══════════════════════════════════════════════════════════"
echo "  🔒 Security Audit — H1-AI"
echo "  🕐 $(date)"
echo "═══════════════════════════════════════════════════════════"

PSQL="PGPASSWORD=h1ai_pass psql -h localhost -U h1ai -d h1ai -P pager=off"

echo ""
echo "▶ 1. المستخدمين والصلاحيات"
sudo -u postgres psql -d h1ai -c "\du" 2>/dev/null

echo ""
echo "▶ 2. صلاحيات المستخدم h1ai على الـ tables"
$PSQL -c "
SELECT 
    grantee, table_name, privilege_type
FROM information_schema.table_privileges
WHERE grantee = 'h1ai'
  AND table_schema = 'public'
ORDER BY table_name, privilege_type;
" | head -40

echo ""
echo "▶ 3. الـ functions الخطيرة (SECURITY DEFINER بدون search_path)"
$PSQL -c "
SELECT 
    p.proname AS function_name,
    CASE WHEN p.prosecdef THEN '⚠️ SECURITY DEFINER' ELSE '✅ SECURITY INVOKER' END AS security,
    pg_get_functiondef(p.oid) LIKE '%SET search_path%' AS has_safe_search_path
FROM pg_proc p
JOIN pg_namespace n ON p.pronamespace = n.oid
WHERE n.nspname = 'public'
ORDER BY p.prosecdef DESC, p.proname;
"

echo ""
echo "▶ 4. Row Level Security (RLS) — تأكد مفعل على multi-tenant tables"
$PSQL -c "
SELECT 
    schemaname,
    tablename,
    rowsecurity AS rls_enabled,
    (SELECT COUNT(*) FROM pg_policies pp WHERE pp.tablename = t.tablename) AS policy_count
FROM pg_tables t
WHERE schemaname = 'public'
ORDER BY rowsecurity DESC, tablename;
"

echo ""
echo "▶ 5. فحص pg_hba.conf (منع trust/ident)"
sudo cat /etc/postgresql/*/main/pg_hba.conf 2>/dev/null | grep -v '^#' | grep -v '^$'

echo ""
echo "▶ 6. فحص كلمات السر الافتراضية في .env"
cd ~/h1-ai
if [ -f .env ]; then
    echo "  ⚠️  .env موجود — تأكد إنه في .gitignore"
    grep -E "PASSWORD|SECRET|KEY|TOKEN" .env | sed 's/=.*/=***REDACTED***/'
else
    echo "  ℹ️  مفيش .env في الجذر"
fi

echo ""
echo "▶ 7. تأكد .env مش مرفوع على Git"
cd ~/h1-ai
git ls-files | grep -E "\.env|\.pem|\.key|credentials" || echo "  ✅ مفيش ملفات حساسة مرفوعة"

echo ""
echo "▶ 8. فحص الـ API keys المشفرة (لو مخزنة plaintext)"
$PSQL -c "
SELECT 
    COUNT(*) AS total_keys,
    COUNT(*) FILTER (WHERE key_hash IS NULL) AS unhashed,
    COUNT(*) FILTER (WHERE key_hash IS NOT NULL AND LENGTH(key_hash) < 32) AS weak_hash
FROM api_keys;
" 2>/dev/null || echo "  ℹ️  مفيش جدول api_keys أو هيكل مختلف"

echo ""
echo "▶ 9. آخر عمليات تسجيل دخول (audit log)"
$PSQL -c "
SELECT 
    COUNT(*) AS total_events,
    MIN(created_at) AS first_event,
    MAX(created_at) AS last_event
FROM audit_logs;
" 2>/dev/null || echo "  ⚠️  مفيش جدول audit_logs — خطر أمني"

echo ""
echo "▶ 10. SSL/TLS"
$PSQL -c "SHOW ssl;"

echo ""
echo "▶ 11. مين عنده CRUD كامل على كل حاجة"
$PSQL -c "
SELECT 
    table_name,
    STRING_AGG(privilege_type, ', ' ORDER BY privilege_type) AS privs
FROM information_schema.table_privileges
WHERE grantee = 'h1ai' AND table_schema = 'public'
GROUP BY table_name
HAVING COUNT(*) >= 6
ORDER BY table_name;
"

echo ""
echo "═══════════════════════════════════════════════════════════"
