#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 🔧 H1-AI — Master Fix Installer
# ينشئ كل ملفات الإصلاح في مكانها ثم يشغّلها
# ═══════════════════════════════════════════════════════════════
set -e

H1AI_DIR="$HOME/h1-ai"
FIXES_DIR="$H1AI_DIR/scripts/fixes"
BACKEND_DIR="$H1AI_DIR/backend"
VENV_DIR="$HOME/venvs/h1-ai-backend"

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m'
log()  { echo -e "${BLUE}▶ $1${NC}"; }
ok()   { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
err()  { echo -e "${RED}❌ $1${NC}"; }

echo "═══════════════════════════════════════════════════════════════"
echo "  🔧 H1-AI Master Fix Installer"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ═══════════════════════════════════════════════════════════════
# 1. نسخة احتياطية
# ═══════════════════════════════════════════════════════════════
log "[1/14] نسخة احتياطية..."
BACKUP_DIR="$HOME/h1-ai.backup.$(date +%Y%m%d_%H%M%S)"
if [ ! -d "$BACKUP_DIR" ]; then
    cp -r "$H1AI_DIR" "$BACKUP_DIR" 2>/dev/null || warn "تعذّر النسخ الاحتياطي"
    ok "نسخة في: $BACKUP_DIR"
fi

# ═══════════════════════════════════════════════════════════════
# 2. إنشاء مجلدات
# ═══════════════════════════════════════════════════════════════
log "[2/14] إنشاء المجلدات..."
mkdir -p "$FIXES_DIR"
mkdir -p "$BACKEND_DIR/scripts"
mkdir -p "$BACKEND_DIR/middleware"
mkdir -p "$BACKEND_DIR/customer/static"
ok "تم"

# ═══════════════════════════════════════════════════════════════
# 3. إنشاء .env جديد
# ═══════════════════════════════════════════════════════════════
log "[3/14] توليد .env جديد..."
PG_PASS=$(openssl rand -hex 24)
JWT_SEC=$(openssl rand -hex 32)
cat > "$H1AI_DIR/.env" <<EOF
# ═══ Database ═══
POSTGRES_PASSWORD=$PG_PASS

# ═══ LLM Provider ═══
# ⚠️ استبدل هذا بمفتاح Groq حقيقي من https://console.groq.com/keys
LLM_PROVIDER=groq
GROQ_API_KEY=REPLACE_WITH_NEW_GROQ_KEY

# ═══ Security ═══
JWT_SECRET_KEY=$JWT_SEC
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# ═══ Local URLs ═══
DATABASE_URL=postgresql://h1ai:$PG_PASS@localhost:5434/h1ai
REDIS_URL=redis://localhost:6381/0
EOF
chmod 600 "$H1AI_DIR/.env"
ok ".env أُنشئ (chmod 600)"

# ═══════════════════════════════════════════════════════════════
# 4. Fix Dockerfile
# ═══════════════════════════════════════════════════════════════
log "[4/14] إصلاح Dockerfile..."
cat > "$BACKEND_DIR/Dockerfile" <<'DOCKERFILE_EOF'
FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
DOCKERFILE_EOF
ok "Dockerfile محدّث"

# ═══════════════════════════════════════════════════════════════
# 5. Fix docker-compose.yml
# ═══════════════════════════════════════════════════════════════
log "[5/14] إصلاح docker-compose.yml..."
cat > "$H1AI_DIR/docker-compose.yml" <<'COMPOSE_EOF'
version: '3.9'

services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: h1ai-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: h1ai
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}
      POSTGRES_DB: h1ai
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backend/migrations:/docker-entrypoint-initdb.d:ro
    ports:
      - "5434:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U h1ai"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: h1ai-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    ports:
      - "6381:6379"
    volumes:
      - redis_data:/data

  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: h1ai-api
    restart: unless-stopped
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql://h1ai:${POSTGRES_PASSWORD}@postgres:5432/h1ai
      REDIS_URL: redis://redis:6379/0
      LLM_PROVIDER: ${LLM_PROVIDER:-groq}
      GROQ_API_KEY: ${GROQ_API_KEY}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
    ports:
      - "8200:8000"
    volumes:
      - ./backend:/app
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2

  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: h1ai-tunnel
    restart: unless-stopped
    depends_on:
      - api
    command: tunnel --url http://api:8000 --no-autoupdate

volumes:
  postgres_data:
  redis_data:
COMPOSE_EOF
ok "docker-compose محدّث"

# ═══════════════════════════════════════════════════════════════
# 6. Fix systemd h1ai.service
# ═══════════════════════════════════════════════════════════════
log "[6/14] إصلاح h1ai.service..."
sudo tee /etc/systemd/system/h1ai.service > /dev/null <<SYSTEMD_EOF
[Unit]
Description=H1-AI Backend API
After=network.target

[Service]
Type=simple
User=h
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$VENV_DIR/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=-$H1AI_DIR/.env
ExecStart=$VENV_DIR/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
SYSTEMD_EOF

sudo tee /etc/systemd/system/h1ai-health.service > /dev/null <<'HEALTH_EOF'
[Unit]
Description=H1-AI Health Check
After=h1ai.service

[Service]
Type=oneshot
User=h
ExecStart=/usr/bin/curl -fsS http://localhost:8000/health
HEALTH_EOF

sudo systemctl daemon-reload
ok "systemd محدّث"

# ═══════════════════════════════════════════════════════════════
# 7. إنشاء login.html
# ═══════════════════════════════════════════════════════════════
log "[7/14] إنشاء login.html..."
cat > "$BACKEND_DIR/customer/static/login.html" <<'HTML_EOF'
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>H1-AI — تسجيل الدخول</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: -apple-system, "Segoe UI", Tahoma, sans-serif;
      background: linear-gradient(135deg, #0f766e 0%, #14b8a6 100%);
      min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
    .card { background: #fff; border-radius: 16px; padding: 40px;
      box-shadow: 0 20px 60px rgba(0,0,0,0.3); width: 100%; max-width: 400px; }
    h1 { color: #0f766e; text-align: center; margin-bottom: 8px; font-size: 28px; }
    .sub { text-align: center; color: #64748b; margin-bottom: 32px; font-size: 14px; }
    label { display: block; margin-bottom: 6px; color: #334155; font-size: 14px; font-weight: 600; }
    input { width: 100%; padding: 12px 14px; border: 2px solid #e2e8f0;
      border-radius: 8px; font-size: 15px; margin-bottom: 18px; }
    input:focus { outline: none; border-color: #14b8a6; }
    button { width: 100%; padding: 13px; background: #0f766e; color: #fff;
      border: none; border-radius: 8px; font-size: 16px; font-weight: 600; cursor: pointer; }
    button:hover { background: #115e59; }
    button:disabled { background: #94a3b8; cursor: not-allowed; }
    .error { color: #dc2626; font-size: 13px; margin-bottom: 14px; display: none; }
    .error.show { display: block; }
    .footer { text-align: center; margin-top: 24px; font-size: 13px; color: #64748b; }
    .footer a { color: #0f766e; text-decoration: none; font-weight: 600; }
  </style>
</head>
<body>
  <div class="card">
    <h1>🏥 H1-AI</h1>
    <p class="sub">مساعد الصيدلية الذكي</p>
    <div class="error" id="error"></div>
    <form id="loginForm">
      <label for="username">اسم المستخدم</label>
      <input type="text" id="username" name="username" required>
      <label for="password">كلمة المرور</label>
      <input type="password" id="password" name="password" required>
      <button type="submit" id="submitBtn">دخول</button>
    </form>
    <div class="footer">ليس لديك حساب؟ <a href="/register">سجّل الآن</a></div>
  </div>
  <script>
    const form = document.getElementById('loginForm');
    const err  = document.getElementById('error');
    const btn  = document.getElementById('submitBtn');
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      err.classList.remove('show');
      btn.disabled = true; btn.textContent = 'جاري الدخول...';
      try {
        const r = await fetch('/v1/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: form.username.value, password: form.password.value }),
        });
        if (!r.ok) throw new Error((await r.json().catch(()=>({}))).detail || 'فشل تسجيل الدخول');
        const data = await r.json();
        localStorage.setItem('h1ai_token', data.access_token);
        window.location.href = '/admin/dashboard';
      } catch (e) {
        err.textContent = e.message; err.classList.add('show');
      } finally {
        btn.disabled = false; btn.textContent = 'دخول';
      }
    });
  </script>
</body>
</html>
HTML_EOF
ok "login.html أُنشئ"

# ═══════════════════════════════════════════════════════════════
# 8. Fix pharmacies table
# ═══════════════════════════════════════════════════════════════
log "[8/14] إنشاء fix_pharmacies_table.sql..."
cat > "$BACKEND_DIR/scripts/fix_pharmacies_table.sql" <<'SQL_EOF'
CREATE TABLE IF NOT EXISTS pharmacies (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    slug            VARCHAR(255) UNIQUE NOT NULL,
    phone           VARCHAR(32),
    address         TEXT,
    city            VARCHAR(128),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pharmacies_slug ON pharmacies(slug);
CREATE INDEX IF NOT EXISTS idx_pharmacies_name ON pharmacies(LOWER(name));

INSERT INTO pharmacies (name, slug, phone)
VALUES ('H1-AI Default', 'h1-ai-default', '+20000000000')
ON CONFLICT (slug) DO NOTHING;
SQL_EOF
ok "SQL أُنشئ"

# ═══════════════════════════════════════════════════════════════
# 9. Health methods middleware
# ═══════════════════════════════════════════════════════════════
log "[9/14] إنشاء health_methods.py..."
cat > "$BACKEND_DIR/middleware/health_methods.py" <<'PY_EOF'
"""يسمح بـ HEAD و OPTIONS على endpoints الفحص"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp


class HealthMethodsMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request, call_next):
        path = request.url.path
        if path in ("/health", "/healthz", "/health/live", "/health/ready"):
            if request.method == "HEAD":
                new_scope = dict(request.scope)
                new_scope["method"] = "GET"
                response = await call_next.__self__(new_scope, request.receive, lambda m: None)
                return Response(status_code=200, headers={"Allow": "GET, HEAD, OPTIONS"})
            if request.method == "OPTIONS":
                return Response(status_code=204, headers={"Allow": "GET, HEAD, OPTIONS"})
        return await call_next(request)
PY_EOF
ok "middleware أُنشئ"

# ═══════════════════════════════════════════════════════════════
# 10. Groq timeout helper
# ═══════════════════════════════════════════════════════════════
log "[10/14] إنشاء groq_timeout.py..."
cat > "$BACKEND_DIR/middleware/groq_timeout.py" <<'PY_EOF'
"""يضيف timeout + retry لاستدعاءات Groq"""
import asyncio
import logging
from functools import wraps

logger = logging.getLogger(__name__)
GROQ_TIMEOUT_SECONDS = 30
GROQ_MAX_RETRIES = 2


def with_groq_timeout(timeout: int = GROQ_TIMEOUT_SECONDS):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(GROQ_MAX_RETRIES + 1):
                try:
                    return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
                except Exception as e:
                    last_exc = e
                    logger.warning(f"Groq attempt {attempt+1} failed: {e}")
                    if attempt < GROQ_MAX_RETRIES:
                        await asyncio.sleep(2 ** attempt)
            raise last_exc
        return wrapper
    return decorator
PY_EOF
ok "groq_timeout أُنشئ"

# ═══════════════════════════════════════════════════════════════
# 11. Verify script
# ═══════════════════════════════════════════════════════════════
log "[11/14] إنشاء verify.sh..."
cat > "$FIXES_DIR/verify.sh" <<'VERIFY_EOF'
#!/bin/bash
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m'
pass() { echo -e "  ${GREEN}✅ $1${NC}"; }
fail() { echo -e "  ${RED}❌ $1${NC}"; }
warn() { echo -e "  ${YELLOW}⚠️  $1${NC}"; }
head() { echo -e "\n${BLUE}═══ $1 ═══${NC}"; }

head "Services"
for svc in h1ai.service postgresql tailscaled; do
    systemctl is-active --quiet "$svc" 2>/dev/null && pass "$svc" || fail "$svc"
done

head "Docker"
for c in h1ai-postgres h1ai-redis h1ai-api h1ai-tunnel; do
    STATE=$(docker inspect -f '{{.State.Status}}' "$c" 2>/dev/null)
    [ "$STATE" = "running" ] && pass "$c" || warn "$c ($STATE)"
done

head "Endpoints (8000)"
for path in /health /docs /openapi.json /admin/dashboard /login; do
    CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000$path" 2>/dev/null)
    [ "$CODE" = "200" ] && pass "$path → $CODE" || fail "$path → $CODE"
done

head "HEAD /health"
CODE=$(curl -s -I -o /dev/null -w "%{http_code}" "http://localhost:8000/health" 2>/dev/null)
[ "$CODE" = "200" ] && pass "HEAD → 200" || fail "HEAD → $CODE"

head "Database"
docker exec h1ai-postgres psql -U h1ai -d h1ai -c "SELECT 1" >/dev/null 2>&1 && pass "PostgreSQL" || fail "PostgreSQL"
docker exec h1ai-postgres psql -U h1ai -d h1ai -c "\dt" 2>/dev/null | grep -q pharmacies && pass "pharmacies" || warn "pharmacies missing"

head "Redis"
docker exec h1ai-redis redis-cli ping 2>/dev/null | grep -q PONG && pass "Redis" || fail "Redis"

head "Python"
cd ~/h1-ai/backend
source ~/venvs/h1-ai-backend/bin/activate 2>/dev/null
python -c "import main" 2>/dev/null && pass "import main" || fail "import main"
python -c "from main import app; app.openapi()" 2>/dev/null && pass "OpenAPI" || fail "OpenAPI"

head "Security"
[ "$(stat -c '%a' ~/h1-ai/.env 2>/dev/null)" = "600" ] && pass ".env 600" || warn ".env perms"
VERIFY_EOF
chmod +x "$FIXES_DIR/verify.sh"
ok "verify.sh"

# ═══════════════════════════════════════════════════════════════
# 12. Cleanup script
# ═══════════════════════════════════════════════════════════════
log "[12/14] إنشاء cleanup.sh..."
cat > "$FIXES_DIR/cleanup.sh" <<'CLEAN_EOF'
#!/bin/bash
H1AI_DIR="$HOME/h1-ai"
echo "🧹 تنظيف H1-AI..."
find "$H1AI_DIR" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find "$H1AI_DIR" -name "*.pyc" -delete 2>/dev/null || true
find "$H1AI_DIR" -name "*.pyo" -delete 2>/dev/null || true
rm -rf "$H1AI_DIR/backend/.pytest_cache" "$H1AI_DIR/backend/.ruff_cache" 2>/dev/null || true
pip cache purge 2>/dev/null || true
docker system prune -f 2>/dev/null || true
echo "✅ اكتمل"
df -h / | tail -1
CLEAN_EOF
chmod +x "$FIXES_DIR/cleanup.sh"
ok "cleanup.sh"

# ═══════════════════════════════════════════════════════════════
# 13. sysctl + UFW
# ═══════════════════════════════════════════════════════════════
log "[13/14] sysctl + UFW..."
grep -q "vm.overcommit_memory = 1" /etc/sysctl.conf 2>/dev/null || \
    echo "vm.overcommit_memory = 1" | sudo tee -a /etc/sysctl.conf >/dev/null
sudo sysctl vm.overcommit_memory=1 >/dev/null 2>&1 || true
sudo ufw allow out 7844/udp >/dev/null 2>&1 || true
ok "sysctl + UFW"

# ═══════════════════════════════════════════════════════════════
# 14. إعادة التشغيل
# ═══════════════════════════════════════════════════════════════
log "[14/14] إعادة تشغيل الخدمات..."
pkill -9 -f "uvicorn main:app" 2>/dev/null || true
sudo systemctl stop h1ai.service 2>/dev/null || true
sudo systemctl start h1ai.service 2>/dev/null || warn "systemd فشل — ستحتاج تشغيل يدوي"
sleep 3

cd "$H1AI_DIR"
# لا نعيد docker compose up تلقائياً لأن .env فيه مفتاح placeholder
warn "لم يتم تشغيل Docker — عدّل GROQ_API_KEY في .env ثم: docker compose up -d"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ اكتمل تركيب الإصلاحات${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📁 الملفات المُنشأة:"
echo "   $BACKEND_DIR/Dockerfile"
echo "   $BACKEND_DIR/middleware/health_methods.py"
echo "   $BACKEND_DIR/middleware/groq_timeout.py"
echo "   $BACKEND_DIR/customer/static/login.html"
echo "   $BACKEND_DIR/scripts/fix_pharmacies_table.sql"
echo "   $FIXES_DIR/verify.sh"
echo "   $FIXES_DIR/cleanup.sh"
echo "   $H1AI_DIR/docker-compose.yml"
echo "   $H1AI_DIR/.env"
echo ""
echo "🔴 الخطوات التالية الإلزامية:"
echo "  1. عدّل $H1AI_DIR/.env وضع مفتاح Groq حقيقي"
echo "  2. أبطل المفتاح القديم من https://console.groq.com/keys"
echo "  3. شغّل: bash $FIXES_DIR/verify.sh"
echo ""
