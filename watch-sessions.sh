#!/bin/bash
# مراقبة جلسات WhatsApp مباشرة

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

while true; do
    clear
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BOLD}${CYAN}  📱 WhatsApp Sessions Monitor — H1-AI${NC}"
    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${BLUE}🕐 الوقت:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # فحص WhatsApp Service
    SERVICE_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3001/health 2>/dev/null)
    if [ "$SERVICE_STATUS" = "200" ]; then
        echo -e "  ${GREEN}✅ WhatsApp Service: يعمل${NC}"
    else
        echo -e "  ${RED}❌ WhatsApp Service: معطّل${NC}"
        echo ""
        sleep 3
        continue
    fi

    # فحص Backend
    BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health 2>/dev/null)
    if [ "$BACKEND_STATUS" = "200" ]; then
        echo -e "  ${GREEN}✅ Backend API: يعمل${NC}"
    else
        echo -e "  ${RED}❌ Backend API: معطّل${NC}"
    fi
    echo ""

    # جلب الجلسات
    SESSIONS=$(curl -s http://localhost:3001/sessions 2>/dev/null)

    echo -e "${BOLD}${CYAN}─────────────────────────────────────────────────────────${NC}"
    echo -e "${BOLD}  📋 الجلسات${NC}"
    echo -e "${BOLD}${CYAN}─────────────────────────────────────────────────────────${NC}"

    # معالجة JSON
    echo "$SESSIONS" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    sessions = data.get('sessions', [])

    if not sessions:
        print('  لا توجد جلسات')
    else:
        for s in sessions:
            phone = s.get('phone_number', '?')
            status = s.get('status', '?')
            pharmacy = s.get('pharmacy_id', 'None')

            if status == 'connected':
                icon = '🟢'
                color = '\033[0;32m'
            elif status == 'waiting_qr':
                icon = '🟡'
                color = '\033[1;33m'
            elif status == 'disconnected':
                icon = '🔴'
                color = '\033[0;31m'
            else:
                icon = '⚪'
                color = '\033[0m'

            print(f'  {icon} \033[1m{phone}\033[0m')
            print(f'     الحالة: {color}{status}\033[0m')
            print(f'     الصيدلية: {pharmacy}')
            print()
except Exception as e:
    print(f'خطأ: {e}')
    print(sys.stdin.read())
"

    echo -e "${BOLD}${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${YELLOW}للتحديث تلقائياً كل 3 ثواني | Ctrl+C للخروج${NC}"
    echo -e "  ${CYAN}للاتصال الجديد: POST /sessions ${NC}"

    sleep 3
done
