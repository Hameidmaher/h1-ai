#!/bin/bash
# H1-AI Health Check
set -uo pipefail

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'
ok()   { echo -e "  ${GREEN}✅${NC} $*"; }
err()  { echo -e "  ${RED}❌${NC} $*"; }
warn() { echo -e "  ${YELLOW}⚠️${NC}  $*"; }
step() { echo -e "\n${BOLD}${CYAN}═══ $* ═══${NC}"; }

FAIL=0

echo "🏥 H1-AI Health Check — $(date)"
echo "═══════════════════════════════════════════════════════"

# 1. Services
step "Services"
for svc in h1ai-api h1ai-webhook nginx postgresql@17-main; do
    if systemctl is-active --quiet $svc; then
        ok "$svc"
    else
        err "$svc (متوقف!)"
        FAIL=$((FAIL+1))
    fi
done

# 2. Endpoints
step "Endpoints"
check_url() {
    local name="$1" url="$2"
    local code=$(curl -s -o /dev/null -w "%{http_code}" "$url" --max-time 5)
    if [ "$code" = "200" ] || [ "$code" = "307" ] || [ "$code" = "401" ] || [ "$code" = "422" ]; then
        ok "$name → $code"
    else
        err "$name → $code"
        FAIL=$((FAIL+1))
    fi
}

check_url "h1ai-api /health"  "http://localhost:8000/health"
check_url "h1ai-api /admin"   "http://localhost:8000/admin"
check_url "Nginx /"           "http://localhost/"
check_url "Webhook /health"   "http://localhost:9000/health"

# 3. Resources
step "Resources"
DISK=$(df / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$DISK" -lt 85 ]; then
    ok "Disk: $DISK%"
else
    warn "Disk: $DISK% (>85%)"
fi

MEM=$(free | awk '/Mem/ {printf "%.0f", $3/$2*100}')
if [ "$MEM" -lt 85 ]; then
    ok "Memory: $MEM%"
else
    warn "Memory: $MEM%"
fi

LOAD=$(cut -d' ' -f1 /proc/loadavg)
ok "Load: $LOAD"

# 4. Database
step "Database"
if sudo -n -u postgres psql -d h1ai -c "SELECT 1;" > /dev/null 2>&1; then
    SIZE=$(sudo -n -u postgres psql -t -d h1ai -c "SELECT pg_size_pretty(pg_database_size('h1ai'));" | tr -d ' ')
    ok "PostgreSQL ($SIZE)"
else
    err "PostgreSQL query فشل"
    FAIL=$((FAIL+1))
fi

# 5. Backups
step "Backups"
LATEST=$(ls -t /home/h/h1-ai/backups/h1ai-backup-*.tar.gz 2>/dev/null | head -1)
if [ -n "$LATEST" ]; then
    AGE_H=$(( ($(date +%s) - $(stat -c %Y "$LATEST")) / 3600 ))
    if [ $AGE_H -lt 48 ]; then
        ok "آخر backup: $AGE_H ساعة"
    else
        warn "آخر backup: $AGE_H ساعة (>48!)"
    fi
else
    warn "مفيش backups"
fi

# Summary
echo ""
echo "═══════════════════════════════════════════════════════"
if [ $FAIL -eq 0 ]; then
    echo -e "  ${GREEN}${BOLD}✅ كل حاجة سليمة${NC}"
    exit 0
else
    echo -e "  ${RED}${BOLD}❌ $FAIL مشاكل${NC}"
    exit 1
fi
