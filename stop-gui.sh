#!/bin/bash
# ═══════════════════════════════════════════════════════════
# H1-AI — GUI Stop
# ═══════════════════════════════════════════════════════════

H1AI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$H1AI_DIR/logs"

# Kill processes
pkill -f "uvicorn main:app" 2>/dev/null
pkill -f "node server.js" 2>/dev/null

rm -f "$LOG_DIR/backend.pid" "$LOG_DIR/whatsapp.pid"

# Notification
if command -v notify-send > /dev/null; then
    notify-send "H1-AI" "🛑 تم إيقاف النظام" 2>/dev/null
fi

