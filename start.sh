#!/bin/bash
# ═══════════════════════════════════════════════════════════
# H1-AI — One-Click Startup Script
# ═══════════════════════════════════════════════════════════

H1AI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$H1AI_DIR/logs"
mkdir -p "$LOG_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

clear
echo "═══════════════════════════════════════════════════════════"
echo "  🏥 H1-AI — Starting Full Stack"
echo "═══════════════════════════════════════════════════════════"
echo ""

# ─── 1. Check prerequisites ───
echo -e "${BLUE}▶ Checking prerequisites...${NC}"

# Python venv
if [ ! -d "$H1AI_DIR/backend/.venv" ]; then
    echo -e "${RED}❌ Python venv not found at backend/.venv${NC}"
    echo "   Run: cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi
echo -e "${GREEN}✅ Python venv${NC}"

# Node modules
if [ ! -d "$H1AI_DIR/whatsapp-service/node_modules" ]; then
    echo -e "${YELLOW}⚠️  Node modules not found — installing...${NC}"
    cd "$H1AI_DIR/whatsapp-service" && npm install
fi
echo -e "${GREEN}✅ Node modules${NC}"

# ─── 2. Kill existing processes ───
echo ""
echo -e "${BLUE}▶ Stopping old processes...${NC}"

pkill -f "uvicorn main:app" 2>/dev/null && echo "   Killed old backend" || true
pkill -f "node server.js" 2>/dev/null && echo "   Killed old WhatsApp" || true
sleep 1

# ─── 3. Start Backend ───
echo ""
echo -e "${BLUE}▶ Starting Backend (FastAPI)...${NC}"
cd "$H1AI_DIR/backend"
. .venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$LOG_DIR/backend.pid"
echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"

# Wait for backend
echo -n "   Waiting for backend to be ready"
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e " ${GREEN}✅${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# ─── 4. Start WhatsApp Service ───
echo ""
echo -e "${BLUE}▶ Starting WhatsApp Service (Node.js)...${NC}"
cd "$H1AI_DIR/whatsapp-service"
nohup node server.js > "$LOG_DIR/whatsapp.log" 2>&1 &
WA_PID=$!
echo "$WA_PID" > "$LOG_DIR/whatsapp.pid"
echo -e "${GREEN}✅ WhatsApp started (PID: $WA_PID)${NC}"

# Wait for WhatsApp
echo -n "   Waiting for WhatsApp"
for i in {1..20}; do
    if curl -s http://localhost:3001/health > /dev/null 2>&1; then
        echo -e " ${GREEN}✅${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# ─── 5. Health Check ───
echo ""
echo -e "${BLUE}▶ System Status:${NC}"
echo ""

# Backend
BACKEND_STATUS=$(curl -s http://localhost:8000/health 2>/dev/null)
if echo "$BACKEND_STATUS" | grep -q "healthy"; then
    echo -e "${GREEN}✅ Backend${NC}         http://localhost:8000"
    echo -e "   📖 Docs:        http://localhost:8000/docs"
    echo -e "   🎛️  Admin:       http://localhost:8000/admin"
else
    echo -e "${RED}❌ Backend failed${NC} — check logs: $LOG_DIR/backend.log"
fi

# WhatsApp
WA_STATUS=$(curl -s http://localhost:3001/health 2>/dev/null)
if [ -n "$WA_STATUS" ]; then
    echo -e "${GREEN}✅ WhatsApp${NC}        http://localhost:3001"
else
    echo -e "${YELLOW}⚠️  WhatsApp starting${NC} — check logs: $LOG_DIR/whatsapp.log"
fi

# ─── 6. Pipeline test ───
echo ""
echo -e "${BLUE}▶ Quick Pipeline Test:${NC}"
TEST_RESULT=$(curl -s -X POST http://localhost:8000/webhook/v2/incoming \
    -H "Content-Type: application/json" \
    -d '{"phone": "+201000000000", "message": "test from start.sh", "name": "System"}' 2>/dev/null)

if echo "$TEST_RESULT" | grep -q "success"; then
    echo -e "${GREEN}✅ Pipeline works${NC}"
else
    echo -e "${YELLOW}⚠️  Pipeline test skipped${NC}"
fi

# ─── 7. Logs shortcut ───
echo ""
echo "═══════════════════════════════════════════════════════════"
echo -e "  ${GREEN}✅ H1-AI is running!${NC}"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo -e "${CYAN}📊 Quick Commands:${NC}"
echo "   Stop:     ./stop.sh"
echo "   Logs:     tail -f logs/backend.log"
echo "              tail -f logs/whatsapp.log"
echo "   Test:     ./test.sh"
echo ""
echo -e "${CYAN}📱 WhatsApp:${NC}"
echo "   امسح QR من logs/whatsapp.log"
echo "   tail -f $LOG_DIR/whatsapp.log"
echo ""

# ─── 8. Open browser ───
if command -v xdg-open > /dev/null; then
    sleep 2
    xdg-open http://localhost:8000/docs > /dev/null 2>&1 &
fi

echo "═══════════════════════════════════════════════════════════"
echo "  Press Ctrl+C to see this again, or ./stop.sh to stop"
echo "═══════════════════════════════════════════════════════════"
