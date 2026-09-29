#!/bin/bash
H1AI="$HOME/h1-ai"
WS="$H1AI/whatsapp-service"

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
err()  { echo -e "${RED}❌ $1${NC}"; }
head() { echo -e "\n${CYAN}═══ $1 ═══${NC}"; }

clear
echo "═══════════════════════════════════════════════════════════════"
echo "  🔍 WhatsApp QR Diagnosis"
echo "═══════════════════════════════════════════════════════════════"

head "1. الخدمة"
systemctl is-active h1ai-whatsapp.service && ok "active" || err "inactive"

head "2. Health"
curl -s http://localhost:3001/health | python3 -m json.tool

head "3. Sessions"
curl -s http://localhost:3001/sessions | python3 -m json.tool

head "4. Available endpoints"
curl -s http://localhost:3001/ | python3 -m json.tool 2>/dev/null || \
    curl -s http://localhost:3001/ | head -50

head "5. QR endpoints (probing)"
for path in \
  "/sessions/qr" \
  "/sessions/+201001234567/qr" \
  "/sessions/+201001234567/qr.png" \
  "/qr" \
  "/qr.png" \
  "/api/qr" \
  "/whatsapp/qr"; do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3001$path" 2>/dev/null)
    SIZE=$(curl -s "http://localhost:3001$path" 2>/dev/null | wc -c)
    if [ "$CODE" = "200" ]; then
        ok "$CODE → $path ($SIZE bytes)"
    else
        echo "   $CODE → $path"
    fi
done

head "6. Session files"
if [ -d "$WS/sessions" ]; then
    find "$WS/sessions" -type f 2>/dev/null | head -20
    echo ""
    echo "Total size: $(du -sh $WS/sessions 2>/dev/null | cut -f1)"
else
    warn "sessions directory غير موجود"
fi

head "7. QR files"
find "$WS" -name "*qr*" -o -name "*.png" 2>/dev/null | head -10

head "8. Recent log (QR-related)"
sudo journalctl -u h1ai-whatsapp.service -n 100 --no-pager 2>/dev/null | \
    grep -iE "qr|scan|code|ready|connected" | tail -15

head "9. service.log"
if [ -f "$WS/service.log" ]; then
    tail -30 "$WS/service.log" | grep -iE "qr|scan|code|ready|connected" | tail -15
fi

head "10. Node processes"
ps aux | grep -E "node.*server" | grep -v grep

echo ""
echo "═══════════════════════════════════════════════════════════════"
