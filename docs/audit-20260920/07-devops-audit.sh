#!/bin/bash
cd ~/h1-ai

echo "▶ 1. Git status وحجم الـ repo"
git status --short
echo ""
git count-objects -vH

echo ""
echo "▶ 2. آخر 10 commits"
git log --oneline -10

echo ""
echo "▶ 3. الملفات غير المرفوعة (uncommitted)"
git status --short | wc -l

echo ""
echo "▶ 4. Branches"
git branch -a

echo ""
echo "▶ 5. حجم الـ repo (يفضل < 100MB)"
du -sh .git

echo ""
echo "▶ 6. ملفات كبيرة في git history"
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' \
    | awk '/^blob/ {print substr($0,6)}' | sort -rn -k2 | head -10

echo ""
echo "▶ 7. CI/CD configuration"
ls -la .github/workflows/ 2>/dev/null || echo "  ⚠️  مفيش GitHub Actions"
ls -la .gitlab-ci.yml 2>/dev/null || echo "  ℹ️  مفيش GitLab CI"

echo ""
echo "▶ 8. Docker/Compose"
ls -la Dockerfile* docker-compose*.yml 2>/dev/null || echo "  ℹ️  مفيش Docker"

echo ""
echo "▶ 9. مفيش .gitignore entries مهمة"
if [ -f .gitignore ]; then
    for pattern in ".env" "*.log" "node_modules" "__pycache__" "*.pyc" ".venv"; do
        grep -q "^$pattern" .gitignore && echo "  ✅ $pattern" || echo "  ⚠️  Missing: $pattern"
    done
else
    echo "  🔴 مفيش .gitignore!"
fi

echo ""
echo "▶ 10. Dependencies audit"
if [ -f requirements.txt ]; then
    echo "  Python packages: $(wc -l < requirements.txt)"
    pip-audit -r requirements.txt 2>/dev/null | head -20 || echo "  ℹ️  pip-audit مش مثبت"
fi
if [ -f package.json ]; then
    echo "  Node packages: $(jq '.dependencies | length' package.json 2>/dev/null)"
    npm audit --production 2>/dev/null | head -20
fi
