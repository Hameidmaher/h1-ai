#!/bin/bash
# ═══════════════════════════════════════════════════════════
# H1-AI — GUI Startup (Desktop Launcher)
# ═══════════════════════════════════════════════════════════

H1AI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$H1AI_DIR/logs"
mkdir -p "$LOG_DIR"

# ─── Terminal emulator detection ───
if command -v gnome-terminal > /dev/null; then
    TERM_CMD="gnome-terminal --"
elif command -v konsole > /dev/null; then
    TERM_CMD="konsole --"
elif command -v xfce4-terminal > /dev/null; then
    TERM_CMD="xfce4-terminal --"
elif command -v xterm > /dev/null; then
    TERM_CMD="xterm -e"
else
    TERM_CMD=""
fi

# ─── Notification function ───
notify() {
    if command -v notify-send > /dev/null; then
        notify-send "H1-AI" "$1" -i "$H1AI_DIR/brand/logo.svg" 2>/dev/null || \
        notify-send "H1-AI" "$1" 2>/dev/null
    fi
}

# ─── Stop old processes ───
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "node server.js" 2>/dev/null
sleep 1

# ─── Start Backend ───
cd "$H1AI_DIR/backend"
. .venv/bin/activate
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > "$LOG_DIR/backend.log" 2>&1 &
BACKEND_PID=$!
echo "$BACKEND_PID" > "$LOG_DIR/backend.pid"

# Wait
for i in {1..30}; do
    curl -s http://localhost:8000/health > /dev/null 2>&1 && break
    sleep 1
done

# ─── Start WhatsApp ───
cd "$H1AI_DIR/whatsapp-service"
nohup node server.js > "$LOG_DIR/whatsapp.log" 2>&1 &
WA_PID=$!
echo "$WA_PID" > "$LOG_DIR/whatsapp.pid"

sleep 3

# ─── Check health ───
if curl -s http://localhost:8000/health | grep -q "healthy"; then
    notify "✅ H1-AI يعمل — فتح Dashboard..."
    sleep 1
    xdg-open http://localhost:8000/admin/dashboard > /dev/null 2>&1 &
else
    notify "❌ فشل تشغيل H1-AI — راجع logs"
    if [ -n "$TERM_CMD" ]; then
        $TERM_CMD tail -30 "$LOG_DIR/backend.log"
    fi
fi

