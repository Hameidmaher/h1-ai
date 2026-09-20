#!/bin/bash
PSQL="PGPASSWORD=h1ai_pass psql -h localhost -U h1ai -d h1ai -P pager=off"

echo "▶ 1. Orphaned rows (FK orphan check)"
$PSQL -c "
SELECT 
    'messages.user_id' AS check_name,
    COUNT(*) AS orphans
FROM messages m
LEFT JOIN users u ON m.user_id = u.id
WHERE m.user_id IS NOT NULL AND u.id IS NULL
UNION ALL
SELECT 
    'messages.pharmacy_id',
    COUNT(*)
FROM messages m
LEFT JOIN pharmacies p ON m.pharmacy_id = p.id
WHERE m.pharmacy_id IS NOT NULL AND p.id IS NULL;
" 2>/dev/null

echo ""
echo "▶ 2. NULL violations (أعمدة المفروض تكون مملوءة)"
$PSQL -c "
SELECT 
    'messages.content' AS column, COUNT(*) AS nulls 
FROM messages WHERE content IS NULL OR content = ''
UNION ALL
SELECT 'users.email', COUNT(*) FROM users WHERE email IS NULL OR email = ''
UNION ALL
SELECT 'products.name', COUNT(*) FROM products WHERE name IS NULL OR name = '';
" 2>/dev/null

echo ""
echo "▶ 3. Duplicates (تكرار في حقول unique)"
$PSQL -c "
SELECT email, COUNT(*) 
FROM users 
GROUP BY email 
HAVING COUNT(*) > 1;
"

echo ""
echo "▶ 4. تواريخ غير منطقية"
$PSQL -c "
SELECT 'created_at > updated_at' AS check_name, COUNT(*) FROM users WHERE created_at > updated_at
UNION ALL
SELECT 'created_at في المستقبل', COUNT(*) FROM users WHERE created_at > now()
UNION ALL
SELECT 'updated_at في المستقبل', COUNT(*) FROM users WHERE updated_at > now() + interval '1 hour';
" 2>/dev/null

echo ""
echo "▶ 5. قيم direction/distribution"
$PSQL -c "
SELECT direction, COUNT(*) 
FROM messages 
GROUP BY direction 
ORDER BY COUNT(*) DESC;
"

echo ""
echo "▶ 6. منطقية الاشتراكات"
$PSQL -c "
SELECT 
    status,
    COUNT(*) AS cnt,
    MIN(created_at) AS oldest,
    MAX(created_at) AS newest
FROM subscriptions
GROUP BY status
ORDER BY cnt DESC;
"

echo ""
echo "▶ 7. الفواتير المعلقة"
$PSQL -c "
SELECT 
    status,
    COUNT(*) AS cnt,
    SUM(amount) AS total_amount
FROM invoices
GROUP BY status;
" 2>/dev/null
