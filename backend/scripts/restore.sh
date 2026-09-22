#!/bin/bash
set -euo pipefail

if [ $# -lt 1 ]; then
    echo "الاستخدام: $0 <backup-file.tar.gz>"
    echo ""
    echo "النسخ المتوفرة:"
    ls -lh /home/h/h1-ai/backups/h1ai-backup-*.tar.gz 2>/dev/null | tail -10
    exit 1
fi

BACKUP="$1"
BACKUP_DIR="/home/h/h1-ai/backups"
BACKEND_DIR="/home/h/h1-ai/backend"

[ -f "$BACKUP" ] || BACKUP="$BACKUP_DIR/$1"

if [ ! -f "$BACKUP" ]; then
    echo "❌ الملف مش موجود: $BACKUP"
    exit 1
fi

echo "⚠️  هتستبدل البيانات الحالية بـ $BACKUP"
read -p "متأكد؟ (اكتب yes): " confirm
[ "$confirm" = "yes" ] || { echo "❌ اتلغى"; exit 1; }

TEMP="/tmp/restore-$$"
mkdir -p "$TEMP"
tar xzf "$BACKUP" -C "$TEMP"
BASE="$TEMP/$(ls $TEMP | head -1)"

echo "⏸️  وقف الخدمات..."
sudo systemctl stop h1ai-api h1ai-webhook

echo "💾 backup للنسخة الحالية..."
sudo -u postgres pg_dump h1ai | gzip > "/home/h/h1-ai/backups/pre-restore-$(date +%s).sql.gz"

echo "🔄 استرجاع DB..."
sudo -u postgres psql -c "DROP DATABASE IF EXISTS h1ai;"
sudo -u postgres psql -c "CREATE DATABASE h1ai;"
gunzip -c "$BASE/db/h1ai.sql.gz" | sudo -u postgres psql h1ai

echo "🔄 استرجاع .env..."
[ -f "$BASE/code/.env" ] && cp "$BASE/code/.env" "$BACKEND_DIR/.env" && chmod 600 "$BACKEND_DIR/.env"

echo "▶️  تشغيل الخدمات..."
sudo systemctl start h1ai-api h1ai-webhook

rm -rf "$TEMP"
echo "✅ تم الاسترجاع"
