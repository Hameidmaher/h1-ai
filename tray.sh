#!/bin/bash
# H1-AI System Tray

H1AI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

STATUS="🟢"
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    STATUS="🔴"
fi

yad --notification \
    --image="$H1AI_DIR/brand/logo.svg" \
    --text="H1-AI $STATUS" \
    --menu="فتح Dashboard!xdg-open http://localhost:8000/admin/dashboard|تشغيل!bash $H1AI_DIR/start-gui.sh|إيقاف!bash $H1AI_DIR/stop-gui.sh|عرض Logs!gnome-terminal -- tail -f $H1AI_DIR/logs/backend.log|" \
    --command="xdg-open http://localhost:8000/admin/dashboard"
