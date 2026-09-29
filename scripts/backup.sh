#!/bin/bash
# H1-AI Automated Backup

BACKUP_DIR="$HOME/h1-ai-backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="h1-ai-$TIMESTAMP"

mkdir -p "$BACKUP_DIR"

echo "📦 Creating backup: $BACKUP_NAME"

# 1. Archive project (exclude venv, node_modules)
cd ~
tar --exclude='h1-ai/backend/.venv' \
    --exclude='h1-ai/whatsapp-service/node_modules' \
    --exclude='h1-ai/.git' \
    --exclude='h1-ai/logs' \
    --exclude='h1-ai/**/__pycache__' \
    --exclude='h1-ai/tests/load/*.csv' \
    -czf "$BACKUP_DIR/$BACKUP_NAME.tar.gz" h1-ai/

# 2. Backup DB separately
cp ~/h1-ai/backend/h1ai.db "$BACKUP_DIR/$BACKUP_NAME.db" 2>/dev/null

# 3. Backup .env (encrypted)
if command -v openssl > /dev/null; then
    openssl enc -aes-256-cbc -salt -pbkdf2 \
        -in ~/h1-ai/backend/.env \
        -out "$BACKUP_DIR/$BACKUP_NAME.env.enc" \
        -pass pass:"h1ai-backup-key"
fi

# 4. Cleanup old backups (keep last 7)
ls -t "$BACKUP_DIR"/h1-ai-*.tar.gz 2>/dev/null | tail -n +8 | xargs rm -f 2>/dev/null

# 5. Info
SIZE=$(du -h "$BACKUP_DIR/$BACKUP_NAME.tar.gz" | cut -f1)
echo ""
echo "✅ Backup created: $BACKUP_NAME.tar.gz ($SIZE)"
echo "📁 Location: $BACKUP_DIR"
echo "📊 Total backups: $(ls -1 $BACKUP_DIR/h1-ai-*.tar.gz 2>/dev/null | wc -l)"
