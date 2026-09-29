#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 🚀 H1-AI — Master Optimization Script
# ═══════════════════════════════════════════════════════════════
set -e

H1AI="$HOME/h1-ai"
BACKEND="$H1AI/backend"
ENV_FILE="$H1AI/.env"
VENV="$HOME/venvs/h1-ai-backend"

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'
log()  { echo -e "${BLUE}▶ $1${NC}"; }
ok()   { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
err()  { echo -e "${RED}❌ $1${NC}"; }
head() { echo -e "\n${CYAN}═══ $1 ═══${NC}"; }

clear
echo "═══════════════════════════════════════════════════════════════"
echo "  🚀 H1-AI Master Optimization"
echo "═══════════════════════════════════════════════════════════════"

# ───────────────────────────────────────────────────────────────
# [1/10] نسخة احتياطية
# ───────────────────────────────────────────────────────────────
head "[1/10] نسخة احتياطية"
BK="$HOME/h1ai-opt-backup-$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BK"
cp "$ENV_FILE" "$BK/.env.bak" 2>/dev/null || true
cp /etc/systemd/system/h1ai.service "$BK/h1ai.service.bak" 2>/dev/null || true
ok "النسخة في: $BK"

# ───────────────────────────────────────────────────────────────
# [2/10] إصلاح .env (منافذ + مفاتيح)
# ───────────────────────────────────────────────────────────────
head "[2/10] إصلاح .env"
if [ -f "$ENV_FILE" ]; then
    # استبدل منافذ Docker القديمة بمنافذ النظام
    sed -i 's|localhost:5434|localhost:5432|g' "$ENV_FILE"
    sed -i 's|localhost:6381|localhost:6379|g' "$ENV_FILE"

    # تحقق من مفتاح Groq
    if grep -q "REPLACE_WITH_NEW_GROQ_KEY" "$ENV_FILE"; then
        warn "GROQ_API_KEY لا يزال placeholder"
        warn "عدّل يدوياً: nano $ENV_FILE"
    else
        ok "GROQ_API_KEY موجود"
    fi

    chmod 600 "$ENV_FILE"
    ok ".env محدّث (5432, 6379)"
else
    err ".env غير موجود!"
fi

# ───────────────────────────────────────────────────────────────
# [3/10] تنظيف الملفات المؤقتة
# ───────────────────────────────────────────────────────────────
head "[3/10] تنظيف الملفات المؤقتة"
find "$H1AI" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find "$H1AI" -name "*.pyc" -delete 2>/dev/null || true
find "$H1AI" -name "*.pyo" -delete 2>/dev/null || true
rm -rf "$BACKEND/.pytest_cache" "$BACKEND/.ruff_cache" "$BACKEND/.mypy_cache" 2>/dev/null || true
pip cache purge >/dev/null 2>&1 || true
ok "تم تنظيف __pycache__, .pyc, pip cache"

# ───────────────────────────────────────────────────────────────
# [4/10] تقليم logs قديمة
# ───────────────────────────────────────────────────────────────
head "[4/10] تقليم logs"
LOG_DIR="$BACKEND/logs"
if [ -d "$LOG_DIR" ]; then
    for log_file in "$LOG_DIR"/*.log; do
        if [ -f "$log_file" ]; then
            SIZE=$(stat -c%s "$log_file" 2>/dev/null || echo 0)
            if [ "$SIZE" -gt 10485760 ]; then  # > 10MB
                tail -1000 "$log_file" > "$log_file.tmp"
                mv "$log_file.tmp" "$log_file"
                ok "$(basename $log_file): قُلّم"
            fi
        fi
    done
fi
sudo truncate -s 0 /var/log/h1ai.log 2>/dev/null || true
ok "logs نظيفة"

# ───────────────────────────────────────────────────────────────
# [5/10] تحسينات systemd لـ h1ai.service
# ───────────────────────────────────────────────────────────────
head "[5/10] تحسينات systemd"

# تحقق من وجود مجلد override
sudo mkdir -p /etc/systemd/system/h1ai.service.d

sudo tee /etc/systemd/system/h1ai.service.d/optimize.conf > /dev/null <<SYSD_EOF
[Service]
# إعادة تشغيل تلقائية عند الفشل
Restart=always
RestartSec=5

# Resource limits
LimitNOFILE=65536
LimitNPROC=4096

# Performance tuning
Environment="PYTHONUNBUFFERED=1"
Environment="PYTHONDONTWRITEBYTECODE=1"
Environment="PYTHONOPTIMIZE=2"

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=h1ai-api

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=$H1AI $BACKEND/logs $BACKEND/data

# Working directory
WorkingDirectory=$BACKEND
SYSD_EOF

sudo systemctl daemon-reload
ok "systemd محسّن (security + performance)"

# ───────────────────────────────────────────────────────────────
# [6/10] تحسين cloudflared
# ───────────────────────────────────────────────────────────────
head "[6/10] تحسين cloudflared"

# أوقف كل cloudflared داخل الـ container
docker exec h1ai-tunnel pkill cloudflared 2>/dev/null || true
docker restart h1ai-tunnel
sleep 3

# اسمح بـ QUIC
sudo ufw allow out 7844/udp >/dev/null 2>&1 || true
sudo ufw allow in 7844/udp >/dev/null 2>&1 || true

# تحقق
sleep 5
if docker ps | grep -q h1ai-tunnel; then
    ok "cloudflared يعمل"
else
    err "cloudflared لا يعمل"
fi

# ───────────────────────────────────────────────────────────────
# [7/10] تحسين Redis
# ───────────────────────────────────────────────────────────────
head "[7/10] تحسين Redis"
if ! grep -q "vm.overcommit_memory = 1" /etc/sysctl.conf 2>/dev/null; then
    echo "vm.overcommit_memory = 1" | sudo tee -a /etc/sysctl.conf >/dev/null
fi
sudo sysctl vm.overcommit_memory=1 >/dev/null 2>&1 || true
ok "vm.overcommit_memory = 1"

# ───────────────────────────────────────────────────────────────
# [8/10] تنظيف ~ والملفات المتبقية
# ───────────────────────────────────────────────────────────────
head "[8/10] تنظيف ~/"
rm -f "$HOME/merge-project-2.sh" 2>/dev/null || true
rm -f "$HOME/merge-project.sh" 2>/dev/null || true

# انقل الملفات الحساسة المتبقية
for f in .h1ai_admin_pass .h1ai_admin_user .h1ai_github_token \
         .h1ai_github_token.save .h1ai_old_tokens.txt; do
    if [ -f "$HOME/$f" ]; then
        mv "$HOME/$f" "$H1AI/.secrets/" 2>/dev/null || true
        chmod 600 "$H1AI/.secrets/$f" 2>/dev/null || true
    fi
done
if [ -d "$HOME/.h1ai-secrets" ]; then
    mv "$HOME/.h1ai-secrets" "$H1AI/.secrets/legacy2" 2>/dev/null || true
    chmod -R 700 "$H1AI/.secrets/legacy2" 2>/dev/null || true
fi

chmod 700 "$H1AI/.secrets"
ok "~/ نظيف"

# ───────────────────────────────────────────────────────────────
# [9/10] فحص الـ imports والـ dependencies
# ───────────────────────────────────────────────────────────────
head "[9/10] فحص Python"
if [ -d "$VENV" ]; then
    source "$VENV/bin/activate"
    cd "$BACKEND"

    if python -c "import main" 2>/dev/null; then
        ok "import main"
    else
        err "import main فشل — راجع يدوياً"
    fi

    # فحص requirements
    if pip check >/dev/null 2>&1; then
        ok "pip check سليم"
    else
        warn "pip check فيه تحذيرات"
    fi
else
    err "venv غير موجود: $VENV"
fi

# ───────────────────────────────────────────────────────────────
# [10/10] إعادة تشغيل + التحقق النهائي
# ───────────────────────────────────────────────────────────────
head "[10/10] إعادة تشغيل + التحقق"

sudo systemctl restart h1ai.service
sleep 6

# فحص الخدمات
SERVICES=(
    "h1ai.service"
    "h1ai-whatsapp.service"
    "postgresql"
    "redis-server"
)
for svc in "${SERVICES[@]}"; do
    if systemctl is-active --quiet "$svc"; then
        ok "$svc"
    else
        err "$svc"
    fi
done

# فحص Endpoints
echo ""
ENDPOINTS=(
    "/health:200"
    "/docs:200"
    "/openapi.json:200"
    "/admin/dashboard:200"
    "/login:200"
    "/v1/products:200"
)
for ep in "${ENDPOINTS[@]}"; do
    PATH_PART="${ep%%:*}"
    EXPECTED="${ep##*:}"
    CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000$PATH_PART" 2>/dev/null)
    if [ "$CODE" = "$EXPECTED" ]; then
        ok "$PATH_PART → $CODE"
    else
        warn "$PATH_PART → $CODE (متوقع $EXPECTED)"
    fi
done

# فحص WhatsApp
WA_STATUS=$(curl -s http://localhost:3001/health 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('status'))" 2>/dev/null || echo "unknown")
if [ "$WA_STATUS" = "running" ]; then
    ok "WhatsApp: running"
else
    warn "WhatsApp: $WA_STATUS"
fi

# فحص DB
if command -v psql >/dev/null 2>&1; then
    if PGPASSWORD=$(grep POSTGRES_PASSWORD "$ENV_FILE" | cut -d= -f2) \
       psql -h localhost -p 5432 -U h1ai -d h1ai -c "SELECT 1" >/dev/null 2>&1; then
        ok "PostgreSQL connection"
    else
        warn "PostgreSQL connection فشل"
    fi
fi

# فحص Redis
if redis-cli -p 6379 ping 2>/dev/null | grep -q PONG; then
    ok "Redis ping"
else
    warn "Redis ping فشل"
fi

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${GREEN}🎉 اكتمل التحسين الشامل${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📊 ملخص:"
echo "   المشروع: $H1AI"
echo "   الحجم:   $(du -sh $H1AI 2>/dev/null | cut -f1)"
echo "   النسخة:  $BK"
echo ""
echo "🌐 الروابط:"
echo "   API:      http://localhost:8000"
echo "   Docs:     http://localhost:8000/docs"
echo "   Admin:    http://localhost:8000/admin/dashboard"
echo "   WhatsApp: http://localhost:3001"
echo ""
echo "🔍 لمتابعة اللوجز:"
echo "   sudo journalctl -u h1ai.service -f"
echo "   docker logs -f h1ai-tunnel"
echo ""
echo "⚠️  تنبيهات:"
grep -q "REPLACE_WITH_NEW_GROQ_KEY" "$ENV_FILE" && echo "   ❌ GROQ_API_KEY لا يزال placeholder" || echo "   ✅ GROQ_API_KEY موجود"
echo "   ℹ️  WhatsApp: waiting_qr (امسح QR)"
echo ""
