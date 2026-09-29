#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 🚨 H1-AI Emergency Fix
# ═══════════════════════════════════════════════════════════════
set -e

H1AI="$HOME/h1-ai"
BACKEND="$H1AI/backend"
WS="$H1AI/whatsapp-service"
VENV="$HOME/venvs/h1-ai-backend"

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'
log()  { echo -e "${BLUE}▶ $1${NC}"; }
ok()   { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
err()  { echo -e "${RED}❌ $1${NC}"; }
head() { echo -e "\n${CYAN}═══ $1 ═══${NC}"; }

echo "═══════════════════════════════════════════════════════════════"
echo "  🚨 H1-AI Emergency Fix"
echo "═══════════════════════════════════════════════════════════════"

# ───────────────────────────────────────────────────────────────
# [1/5] إصلاح agents/tools.py
# ───────────────────────────────────────────────────────────────
head "[1/5] إصلاح agents/tools.py"

TOOLS_FILE="$BACKEND/agents/tools.py"

if [ ! -f "$TOOLS_FILE" ]; then
    err "الملف غير موجود: $TOOLS_FILE"
    exit 1
fi

# نسخة احتياطية
cp "$TOOLS_FILE" "$TOOLS_FILE.backup_$(date +%s)"
ok "نسخة احتياطية محفوظة"

# افحص عدد الدوال @tool
COUNT=$(grep -c "@tool" "$TOOLS_FILE" || echo 0)
echo "   وجدت $COUNT دالة @tool"

# أظهر أول 3 دوال
echo ""
echo "   ─── أول 3 دوال ───"
grep -A 3 "@tool" "$TOOLS_FILE" | head -20
echo ""

echo "   ⚠️  يجب إضافة docstring يدوياً لكل دالة @tool"
echo ""
echo "   للمتابعة، اضغط Enter (سيفتح nano)"
read -p "   أو Ctrl+C للخروج: "

nano "$TOOLS_FILE"

# ───────────────────────────────────────────────────────────────
# [2/5] اختبار import
# ───────────────────────────────────────────────────────────────
head "[2/5] اختبار import"
source "$VENV/bin/activate"
cd "$BACKEND"

if python -c "from agents.tools import CUSTOMER_TOOLS" 2>&1 | grep -q "ValueError\|ImportError\|Traceback"; then
    err "import فشل"
    python -c "from agents.tools import CUSTOMER_TOOLS" 2>&1 | tail -10
    warn "أصلح الأخطاء ثم أعد التشغيل"
else
    ok "import ناجح"
fi

# ───────────────────────────────────────────────────────────────
# [3/5] إعادة تشغيل Backend
# ───────────────────────────────────────────────────────────────
head "[3/5] إعادة تشغيل Backend"
sudo systemctl restart h1ai.service
sleep 8

if curl -s http://localhost:8000/health | grep -q healthy; then
    ok "Backend يعمل"
    curl -s http://localhost:8000/health
else
    err "Backend لا يستجيب"
    sudo journalctl -u h1ai.service -n 20 --no-pager | tail -15
fi

# ───────────────────────────────────────────────────────────────
# [4/5] تنظيف WhatsApp sessions
# ───────────────────────────────────────────────────────────────
head "[4/5] تنظيف WhatsApp sessions"

sudo systemctl stop h1ai-whatsapp.service 2>/dev/null || true
sleep 2

# احذف كل جلسة
rm -rf "$WS/sessions/"* 2>/dev/null || true
rm -rf "$WS/sessions/".* 2>/dev/null || true
ok "كل الجلسات حُذفت"

# تحقق
ls -la "$WS/sessions/" 2>/dev/null || echo "   المجلد فارغ"

# ───────────────────────────────────────────────────────────────
# [5/5] إنشاء QR جديد
# ───────────────────────────────────────────────────────────────
head "[5/5] QR جديد"

echo ""
echo "   ⚠️  سيتم تشغيل Baileys يدوياً"
echo "   امسح QR من الطرفية بالموبايل"
echo "   انتظر رسالة: ✅ connected"
echo "   ثم اضغط Ctrl+C"
echo ""
echo "   للمتابعة، اضغط Enter"
read -p "   أو Ctrl+C للإلغاء: "

cd "$WS"
node server.js
