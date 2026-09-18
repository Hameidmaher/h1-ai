#!/bin/bash
# ═══════════════════════════════════════════════════════════
# H1-AI — Stop All Services
# ═══════════════════════════════════════════════════════════

H1AI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$H1AI_DIR/logs"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo "═══════════════════════════════════════════════════════════"
echo "  🛑 Stopping H1-AI"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Kill by PID files
if [ -f "$LOG_DIR/backend.pid" ]; then
    PID=$(cat "$LOG_DIR/backend.pid")
    kill $PID 2>/dev/null && echo -e "${GREEN}✅ Backend stopped${NC}" || echo "Backend not running"
    rm "$LOG_DIR/backend.pid"
fi

if [ -f "$LOG_DIR/whatsapp.pid" ]; then
    PID=$(cat "$LOG_DIR/whatsapp.pid")
    kill $PID 2>/dev/null && echo -e "${GREEN}✅ WhatsApp stopped${NC}" || echo "WhatsApp not running"
    rm "$LOG_DIR/whatsapp.pid"
fi

# Extra kill
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "node server.js" 2>/dev/null

echo ""
echo -e "${GREEN}✅ All services stopped${NC}"
echo "═══════════════════════════════════════════════════════════"
