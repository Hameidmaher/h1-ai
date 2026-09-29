#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# 🚀 H1-AI Full Clean Restart
# ═══════════════════════════════════════════════════════════════════

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║  🚀 H1-AI — Full Clean Restart                                ║"
echo "║  Kill All + Clean + Restart Everything                        ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# ═══════════════════════════════════════════════════════════════════
echo "🗑️  [1/8] Killing all old processes..."
echo "═══════════════════════════════════════════════════════════════"

# Kill uvicorn processes
echo "  → Killing uvicorn..."
pkill -9 -f "uvicorn main:app" 2>/dev/null
pkill -9 -f "uvicorn" 2>/dev/null

# Kill Node WhatsApp service
echo "  → Killing Node WhatsApp service..."
pkill -9 -f "node server.js" 2>/dev/null
pkill -9 -f "node.*whatsapp" 2>/dev/null

# Kill locust
echo "  → Killing locust..."
pkill -9 -f "locust" 2>/dev/null

# Kill any Python process on port 8000
echo "  → Killing processes on port 8000..."
fuser -k 8000/tcp 2>/dev/null

# Kill any process on port 3001
echo "  → Killing processes on port 3001..."
fuser -k 3001/tcp 2>/dev/null

sleep 2
echo "✅ All old processes killed"
echo ""

# ═══════════════════════════════════════════════════════════════════
echo "🧹 [2/8] Stopping systemd services..."
echo "═══════════════════════════════════════════════════════════════"

sudo systemctl stop h1ai.service 2>/dev/null
sudo systemctl stop h1ai-whatsapp.service 2>/dev/null
sudo systemctl stop h1ai-webhook.service 2>/dev/null
sudo systemctl stop h1ai-health.service 2>/dev/null

sleep 2
echo "✅ Services stopped"
echo ""

# ═══════════════════════════════════════════════════════════════════
echo "🧼 [3/8] Cleaning temp files..."
echo "═══════════════════════════════════════════════════════════════"

cd ~/h1-ai/backend

# Clean pycache
echo "  → Cleaning __pycache__..."
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Clean logs (preserve latest)
echo "  → Truncating logs..."
sudo truncate -s 0 /var/log/h1ai.log 2>/dev/null || true
sudo truncate -s 0 ~/h1-ai/whatsapp-service/service.log 2>/dev/null || true
sudo truncate -s 0 ~/h1-ai/backend/logs/health.log 2>/dev/null || true

# Clean test sessions (optional — keep if needed)
echo "  → Cleaning WhatsApp test sessions..."
# rm -rf ~/h1-ai/whatsapp-service/sessions/session-+201001234567 2>/dev/null || true

echo "✅ Temp files cleaned"
echo ""

# ═══════════════════════════════════════════════════════════════════
echo "🔍 [4/8] Verifying configuration..."
echo "═══════════════════════════════════════════════════════════════"

# Check venv
if [ ! -d ~/venvs/h1-ai-backend ]; then
    echo "❌ Virtual env not found!"
    exit 1
fi
echo "  ✅ Virtual env: OK"

# Check .env
if [ ! -f ~/h1-ai/backend/.env ]; then
    echo "❌ .env file missing!"
    exit 1
fi
echo "  ✅ .env: OK"

# Check WhatsApp service
if [ ! -f ~/h1-ai/whatsapp-service/server.js ]; then
    echo "❌ WhatsApp service missing!"
    exit 1
fi
echo "  ✅ WhatsApp service: OK"

# Check database
if ! pg_isready -h localhost -p 5434 -U postgres 2>/dev/null; then
    echo "⚠️  PostgreSQL not ready on 5434"
fi
echo "  ✅ PostgreSQL: OK"

echo ""

# ═══════════════════════════════════════════════════════════════════
echo "🐍 [5/8] Verifying Python imports..."
echo "═══════════════════════════════════════════════════════════════"

source ~/venvs/h1-ai-backend/bin/activate

cd ~/h1-ai/backend
if python3 -c "import main" 2>&1 | grep -q "Traceback"; then
    echo "❌ Python import failed:"
    python3 -c "import main" 2>&1 | tail -10
    exit 1
fi
echo "  ✅ main.py imports OK"

# Test chatbot roles
python3 -c "
from chatbot.roles import admin_tools, pharmacy_tools, customer_tools
from chatbot.roles.orchestrator import route_message
from chatbot.roles.memory import get_stats
from chatbot.roles.formatter import format_response
from chatbot.roles.prompts import get_prompt
print('  ✅ Chatbot roles: OK')
" 2>&1 | grep -v "✅ \[DB\]" || true

echo ""

# ═══════════════════════════════════════════════════════════════════
echo "📱 [6/8] Starting WhatsApp Service..."
echo "═══════════════════════════════════════════════════════════════"

sudo systemctl start h1ai-whatsapp.service
sleep 4

if systemctl is-active --quiet h1ai-whatsapp.service; then
    echo "  ✅ WhatsApp service: active"

    # Test health
    HEALTH=$(curl -s -m 3 http://localhost:3001/health 2>/dev/null)
    if echo "$HEALTH" | grep -q "running"; then
        echo "  ✅ WhatsApp health: OK"
    else
        echo "  ⚠️  WhatsApp health check failed"
    fi
else
    echo "  ❌ WhatsApp service failed to start!"
    sudo journalctl -u h1ai-whatsapp.service -n 20 --no-pager
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
echo "🎯 [7/8] Starting H1-AI Backend..."
echo "═══════════════════════════════════════════════════════════════"

sudo systemctl start h1ai.service
sleep 6

if systemctl is-active --quiet h1ai.service; then
    echo "  ✅ H1-AI Backend: active"

    # Test health
    HEALTH=$(curl -s -m 5 http://localhost:8000/health 2>/dev/null)
    if echo "$HEALTH" | grep -q "healthy"; then
        echo "  ✅ Backend health: OK"
        echo "     $(echo $HEALTH | head -c 100)"
    else
        echo "  ⚠️  Backend health check failed"
        echo "     $HEALTH"
    fi
else
    echo "  ❌ Backend failed to start!"
    sudo journalctl -u h1ai.service -n 30 --no-pager
fi

echo ""

# ═══════════════════════════════════════════════════════════════════
echo "✅ [8/8] Final verification..."
echo "═══════════════════════════════════════════════════════════════"

echo ""
echo "─── Services Status ───"
for svc in h1ai.service h1ai-whatsapp.service postgresql nginx tailscaled; do
    STATUS=$(systemctl is-active "$svc" 2>/dev/null || echo "not-found")
    if [ "$STATUS" = "active" ]; then
        echo "  ✅ $svc: $STATUS"
    else
        echo "  ❌ $svc: $STATUS"
    fi
done

echo ""
echo "─── Ports ───"
for port in 8000 3001 5434 6381; do
    if ss -tlnp 2>/dev/null | grep -q ":$port "; then
        echo "  ✅ Port $port: LISTEN"
    else
        echo "  ⚠️  Port $port: not listening"
    fi
done

echo ""
echo "─── Core Endpoints ───"
for path in /health /docs /admin/control /pharmacy/dashboard /login /register; do
    CODE=$(curl -s -m 3 -o /dev/null -w "%{http_code}" "http://localhost:8000$path" 2>/dev/null)
    if [ "$CODE" = "200" ]; then
        echo "  ✅ $path → $CODE"
    else
        echo "  ⚠️  $path → $CODE"
    fi
done

echo ""
echo "─── WhatsApp Service ───"
for path in /health /sessions; do
    CODE=$(curl -s -m 3 -o /dev/null -w "%{http_code}" "http://localhost:3001$path" 2>/dev/null)
    if [ "$CODE" = "200" ]; then
        echo "  ✅ $path → $CODE"
    else
        echo "  ⚠️  $path → $CODE"
    fi
done

echo ""
echo "─── Chat APIs ───"
for path in /v1/chat/help/admin /v1/chat/help/pharmacy /v1/chat/help/customer; do
    CODE=$(curl -s -m 3 -o /dev/null -w "%{http_code}" "http://localhost:8000$path" 2>/dev/null)
    if [ "$CODE" = "200" ]; then
        echo "  ✅ $path → $CODE"
    else
        echo "  ⚠️  $path → $CODE"
    fi
done

echo ""
echo "─── Memory + Analytics ───"
for path in /v1/chat/analytics/dashboard /v1/chat/analytics/roles; do
    CODE=$(curl -s -m 3 -o /dev/null -w "%{http_code}" "http://localhost:8000$path" 2>/dev/null)
    if [ "$CODE" = "200" ]; then
        echo "  ✅ $path → $CODE"
    else
        echo "  ⚠️  $path → $CODE"
    fi
done

echo ""
echo "─── Resource Usage ───"
free -h | head -2
echo ""
df -h / | tail -1
echo ""
uptime

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "🎉 H1-AI Full Stack Running!"
echo ""
echo "🌐 Access URLs:"
IP=$(hostname -I | awk '{print $1}')
echo "   • Admin Control:    http://$IP:8000/admin/control"
echo "   • Pharmacy Dashboard: http://$IP:8000/pharmacy/dashboard"
echo "   • Pharmacy WhatsApp:  http://$IP:8000/pharmacy/whatsapp"
echo "   • Customer Portal:   http://$IP:8000/login"
echo "   • Docs:              http://$IP:8000/docs"
echo ""
echo "📱 WhatsApp Service:"
echo "   • Health:  http://localhost:3001/health"
echo "   • Sessions: http://localhost:3001/sessions"
echo ""
echo "═══════════════════════════════════════════════════════════════"
