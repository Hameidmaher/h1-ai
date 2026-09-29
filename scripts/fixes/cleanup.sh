#!/bin/bash
H1AI_DIR="$HOME/h1-ai"
echo "🧹 تنظيف H1-AI..."
find "$H1AI_DIR" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find "$H1AI_DIR" -name "*.pyc" -delete 2>/dev/null || true
find "$H1AI_DIR" -name "*.pyo" -delete 2>/dev/null || true
rm -rf "$H1AI_DIR/backend/.pytest_cache" "$H1AI_DIR/backend/.ruff_cache" 2>/dev/null || true
pip cache purge 2>/dev/null || true
docker system prune -f 2>/dev/null || true
echo "✅ اكتمل"
df -h / | tail -1
