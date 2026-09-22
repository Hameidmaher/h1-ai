#!/bin/bash
# H1-AI Comprehensive Backup
set -euo pipefail

PROJECT_DIR="/home/h/h1-ai"
BACKEND_DIR="$PROJECT_DIR/backend"
BACKUP_DIR="$PROJECT_DIR/backups"
RETENTION=7
TS=$(date +%Y%m%d_%H%M%S)
NAME="h1ai-backup-$TS"
TEMP="/tmp/$NAME"
LOG="$BACKUP_DIR/backup.log"

GREEN='\033[0;32m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'
ok() { echo -e "${GREEN}✅${NC} $*"; }
err() { echo -e "${RED}❌${NC} $*"; }
log() { echo "[$(date '+%F %T')] $*" | tee -a "$LOG"; }

mkdir -p "$BACKUP_DIR" "$TEMP"
log "🚀 بدء: $NAME"

# 1. Database — استخدام connection string مع row_security=off
mkdir -p "$TEMP/db"
DB_URL="postgresql:///?options=-c%20row_security%3Doff"
if sudo -n -u postgres pg_dump --no-owner --no-privileges -d "postgresql://postgres@/h1ai?options=-c%20row_security%3Doff" | gzip > "$TEMP/db/h1ai.sql.gz"; then
    ok "DB: $(du -h "$TEMP/db/h1ai.sql.gz" | cut -f1)"
else
    err "DB dump failed"; exit 1
fi

# 2. Code + .env
mkdir -p "$TEMP/code"
[ -f "$BACKEND_DIR/.env" ] && cp "$BACKEND_DIR/.env" "$TEMP/code/" && chmod 600 "$TEMP/code/.env"
cd "$BACKEND_DIR"
[ -d .git ] && git bundle create "$TEMP/code/repo.bundle" --all 2>/dev/null || true
ok "Code + env"

# 3. Configs
mkdir -p "$TEMP/config"
sudo -n cp /etc/systemd/system/h1ai-*.service "$TEMP/config/" 2>/dev/null || true
sudo -n cp /etc/h1ai/webhook.env "$TEMP/config/" 2>/dev/null || true
sudo -n cp /etc/nginx/sites-available/h1ai "$TEMP/config/nginx.conf" 2>/dev/null || true
sudo -n chown -R $USER:$USER "$TEMP/config" 2>/dev/null || true
sudo -n ufw status numbered > "$TEMP/config/ufw.txt" 2>/dev/null || true
crontab -l > "$TEMP/config/crontab.txt" 2>/dev/null || true
ok "Configs"

# 4. Info
cat > "$TEMP/INFO.txt" << INFOEOF
Timestamp:  $(date)
Hostname:   $(hostname)
Backup:     $NAME

System:
  OS:     $(grep PRETTY_NAME /etc/os-release | cut -d'"' -f2)
  Kernel: $(uname -r)
  RAM:    $(free -h | awk '/Mem/ {print $2}')
  Disk:   $(df -h / | awk 'NR==2 {print $5}')

Services:
$(for s in h1ai-api h1ai-webhook nginx postgresql@17-main; do
    echo "  $s: $(systemctl is-active $s 2>/dev/null || echo unknown)"
done)

Git:
  Branch: $(cd $BACKEND_DIR && git branch --show-current 2>/dev/null)
  Commit: $(cd $BACKEND_DIR && git log --oneline -1 2>/dev/null)
INFOEOF
ok "Info"

# 5. Compress
cd /tmp
tar czf "$BACKUP_DIR/$NAME.tar.gz" "$NAME"
rm -rf "$TEMP"
SIZE=$(du -h "$BACKUP_DIR/$NAME.tar.gz" | cut -f1)
ok "Archive: $SIZE"

# 6. Rotate
find "$BACKUP_DIR" -name "h1ai-backup-*.tar.gz" -mtime +$RETENTION -delete 2>/dev/null || true
REMAIN=$(ls -1 "$BACKUP_DIR"/h1ai-backup-*.tar.gz 2>/dev/null | wc -l)
ok "Retention: $REMAIN نسخة"

# 7. Verify
if tar tzf "$BACKUP_DIR/$NAME.tar.gz" > /dev/null 2>&1; then
    ok "Archive سليم"
else
    err "Archive تالف!"; exit 1
fi

log "✅ اكتمل: $NAME ($SIZE)"
echo ""
echo "📦 $BACKUP_DIR/$NAME.tar.gz ($SIZE)"
