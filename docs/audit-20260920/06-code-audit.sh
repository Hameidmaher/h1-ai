#!/bin/bash
cd ~/h1-ai

echo "▶ 1. فحص naming consistency للـ direction"
echo "--- inbound:" 
grep -rn "inbound" --include="*.py" --include="*.js" --include="*.ts" --include="*.jsx" --include="*.tsx" . 2>/dev/null | wc -l

echo "--- outbound:"
grep -rn "outbound" --include="*.py" --include="*.js" --include="*.ts" . 2>/dev/null | wc -l

echo "--- incoming (القديم):"
grep -rn "incoming" --include="*.py" --include="*.js" --include="*.ts" . 2>/dev/null | wc -l

echo "--- outgoing (القديم):"
grep -rn "outgoing" --include="*.py" --include="*.js" --include="*.ts" . 2>/dev/null | wc -l

echo ""
echo "▶ 2. Secrets hardcoded (خطر أمني خطير!)"
grep -rnE "(password|secret|api_key|token)\s*=\s*['\"][^'\"]{8,}" \
    --include="*.py" --include="*.js" --include="*.ts" --include="*.jsx" --include="*.tsx" \
    --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=venv --exclude-dir=__pycache__ \
    . 2>/dev/null | grep -v ".env" | head -20

echo ""
echo "▶ 3. SQL injection risks (string concat)"
grep -rnE "(execute|query|raw)\s*\(\s*[f'\"]" \
    --include="*.py" --include="*.js" --include="*.ts" \
    --exclude-dir=node_modules --exclude-dir=.git \
    . 2>/dev/null | head -10

echo ""
echo "▶ 4. console.log / print في production code"
grep -rn "console\.log\|print(" \
    --include="*.py" --include="*.js" --include="*.ts" \
    --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=tests \
    . 2>/dev/null | wc -l

echo ""
echo "▶ 5. TODO / FIXME / HACK"
grep -rnE "(TODO|FIXME|HACK|XXX)" \
    --include="*.py" --include="*.js" --include="*.ts" \
    --exclude-dir=node_modules --exclude-dir=.git \
    . 2>/dev/null | wc -l

echo ""
echo "▶ 6. الملفات الأكبر (code smell)"
find . -type f \( -name "*.py" -o -name "*.js" -o -name "*.ts" \) \
    -not -path "./node_modules/*" -not -path "./.git/*" \
    -exec wc -l {} + 2>/dev/null | sort -rn | head -10

echo ""
echo "▶ 7. الملفات بدون tests"
find . -type f -name "*.py" -not -path "./tests/*" -not -path "./.git/*" -not -path "./venv/*" \
    | while read f; do
        test_file="tests/test_$(basename $f)"
        [ ! -f "$test_file" ] && echo "  ⚠️  No test: $f"
    done | head -10
