#!/bin/bash
# H1-AI PostgreSQL Backup Script
# Usage: ./backup-h1ai.sh

set -e

BACKUP_DIR="$HOME/h1-ai/backups"
DB_URL=$(grep "^DATABASE_URL=" "$HOME/h1-ai/backend/.env" | cut -d= -f2-)

# Extract connection info
DB_USER=$(echo "$DB_URL" | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
DB_PASS=$(echo "$DB_URL" | sed -n 's/.*:\/\/[^:]*:\([^@]*\)@.*/\1/p')
DB_HOST=$(echo "$DB_URL" | sed -n 's/.*@\([^:]*\):.*/\1/p')
DB_PORT=$(echo "$DB_URL" | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
DB_NAME=$(echo "$DB_URL" | sed -n 's/.*\/\([^?]*\).*/\1/p')

TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="$BACKUP_DIR/h1ai_${TIMESTAMP}.sql"

mkdir -p "$BACKUP_DIR"

# Create backup
PGPASSWORD="$DB_PASS" pg_dump \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --no-owner \
    --no-acl \
    > "$BACKUP_FILE"

# Compress
gzip -k "$BACKUP_FILE"

# Keep only last 7 backups
find "$BACKUP_DIR" -name "h1ai_*.sql" -mtime +7 -delete
find "$BACKUP_DIR" -name "h1ai_*.sql.gz" -mtime +7 -delete

# Log
echo "[$(date)] Backup: $BACKUP_FILE ($(du -h "$BACKUP_FILE" | cut -f1))" >> "$BACKUP_DIR/backup.log"

# Success
echo "✅ Backup: $BACKUP_FILE"
echo "   Size: $(du -h "$BACKUP_FILE" | cut -f1)"
