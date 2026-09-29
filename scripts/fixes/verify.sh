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
