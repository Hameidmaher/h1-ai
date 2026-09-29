#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 🔬 H1-AI Full Deep Scan
# ═══════════════════════════════════════════════════════════════

TS=$(date +%Y%m%d_%H%M%S)
OUT="$HOME/h1-ai/audit/full_scan_$TS"
mkdir -p "$OUT"/{system,project,git,docker,db,network,logs,security,errors,performance,dev,health}

C_CYAN='\033[0;36m'; C_GREEN='\033[0;32m'; C_YELLOW='\033[1;33m'
C_RED='\033[0;31m'; C_BLUE='\033[0;34m'; C_NC='\033[0m'

step() { echo -e "\n${C_CYAN}▶ $1${C_NC}"; }
ok()   { echo -e "${C_GREEN}  ✅ $1${C_NC}"; }
warn() { echo -e "${C_YELLOW}  ⚠️  $1${C_NC}"; }
err()  { echo -e "${C_RED}  ❌ $1${C_NC}"; }

clear
echo "═══════════════════════════════════════════════════════════════"
echo "  🔬 H1-AI Full Deep Scan"
echo "  Output: $OUT"
echo "═══════════════════════════════════════════════════════════════"

# ───────────────────────────────────────────────────────────────
# 1. SYSTEM INFO
# ───────────────────────────────────────────────────────────────
step "[1/12] System info"

{
  echo "═══ OS ═══"
  cat /etc/os-release
  echo ""
  uname -a
  echo ""
  echo "═══ Kernel ═══"
  uname -r
  echo ""
  echo "═══ Uptime ═══"
  uptime
  echo ""
  echo "═══ Boot time ═══"
  who -b
  echo ""
  echo "═══ Locale ═══"
  locale
  echo ""
  echo "═══ Timezone ═══"
  timedatectl
} > "$OUT/system/os.txt" 2>&1
ok "OS info"

{
  echo "═══ CPU ═══"
  lscpu
  echo ""
  echo "═══ Model ═══"
  cat /proc/cpuinfo | grep -E "model name|MHz|cache" | head -20
  echo ""
  echo "═══ Frequency ═══"
  cat /proc/cpuinfo | grep "MHz" | head -8
  echo ""
  echo "═══ Topology ═══"
  lscpu | grep -E "Socket|Core|Thread|CPU\(s\)"
} > "$OUT/system/cpu.txt" 2>&1
ok "CPU"

{
  echo "═══ Memory ═══"
  free -h
  echo ""
  cat /proc/meminfo | head -30
  echo ""
  echo "═══ Swap ═══"
  swapon --show
  echo ""
  echo "═══ VM stats ═══"
  vmstat 1 3
} > "$OUT/system/memory.txt" 2>&1
ok "Memory"

{
  echo "═══ Block devices ═══"
  lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINT,LABEL,UUID,MODEL
  echo ""
  echo "═══ Disk usage ═══"
  df -h
  echo ""
  echo "═══ Inodes ═══"
  df -i
  echo ""
  echo "═══ SMART (if available) ═══"
  sudo smartctl -a /dev/sda 2>/dev/null | head -50 || echo "smartctl غير مثبت"
} > "$OUT/system/disk.txt" 2>&1
ok "Disk"

{
  echo "═══ PCI devices ═══"
  lspci
  echo ""
  echo "═══ USB devices ═══"
  lsusb
  echo ""
  echo "═══ Temperature ═══"
  sensors 2>/dev/null || echo "lm-sensors غير مثبت"
} > "$OUT/system/hardware.txt" 2>&1
ok "Hardware"

# ───────────────────────────────────────────────────────────────
# 2. PROJECT STRUCTURE
# ───────────────────────────────────────────────────────────────
step "[2/12] Project structure"

{
  echo "═══ Directory tree (max 3 levels) ═══"
  cd ~/h1-ai
  find . -maxdepth 3 -type d 2>/dev/null | grep -v "node_modules\|__pycache__\|\.git\|\.venv\|venv" | sort
  echo ""
  echo "═══ Disk usage per dir ═══"
  du -sh */ 2>/dev/null | sort -h
  echo ""
  echo "═══ Total size ═══"
  du -sh .
} > "$OUT/project/structure.txt" 2>&1
ok "Structure"

{
  echo "═══ File counts by type ═══"
  cd ~/h1-ai
  for ext in py js ts jsx tsx json yaml yml md html css sh sql; do
    count=$(find . -type f -name "*.$ext" 2>/dev/null | grep -v "node_modules\|__pycache__\|\.git" | wc -l)
    echo "$ext: $count"
  done
  echo ""
  echo "═══ Largest files ═══"
  find . -type f -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null | xargs du -h 2>/dev/null | sort -hr | head -30
  echo ""
  echo "═══ Files modified in last 7 days ═══"
  find . -type f -mtime -7 -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/backups/*" -not -path "*/logs/*" 2>/dev/null | head -50
} > "$OUT/project/files.txt" 2>&1
ok "Files"

{
  echo "═══ .env files ═══"
  find ~/h1-ai -name ".env*" -type f 2>/dev/null
  echo ""
  echo "═══ Config files ═══"
  find ~/h1-ai -maxdepth 3 \( -name "*.yaml" -o -name "*.yml" -o -name "*.toml" -o -name "*.ini" -o -name "*.conf" \) -not -path "*/node_modules/*" -not -path "*/.git/*" 2>/dev/null
} > "$OUT/project/configs.txt" 2>&1
ok "Configs"

{
  echo "═══ Python packages ═══"
  source ~/venvs/h1-ai-backend/bin/activate 2>/dev/null
  pip list 2>/dev/null
  echo ""
  echo "═══ pip check ═══"
  pip check 2>&1
  echo ""
  echo "═══ Outdated ═══"
  pip list --outdated 2>/dev/null | head -30
  echo ""
  echo "═══ requirements.txt ═══"
  cat ~/h1-ai/backend/requirements.txt 2>/dev/null
} > "$OUT/project/python.txt" 2>&1
ok "Python packages"

{
  echo "═══ Node.js ═══"
  node --version 2>/dev/null
  npm --version 2>/dev/null
  echo ""
  echo "═══ package.json (whatsapp-service) ═══"
  cat ~/h1-ai/whatsapp-service/package.json 2>/dev/null
  echo ""
  echo "═══ npm outdated ═══"
  cd ~/h1-ai/whatsapp-service && npm outdated 2>/dev/null | head -20
  echo ""
  echo "═══ npm audit ═══"
  cd ~/h1-ai/whatsapp-service && npm audit 2>/dev/null | head -40
} > "$OUT/project/nodejs.txt" 2>&1
ok "Node packages"

# ───────────────────────────────────────────────────────────────
# 3. GIT REPOSITORY
# ───────────────────────────────────────────────────────────────
step "[3/12] Git repository"

{
  cd ~/h1-ai
  echo "═══ Status ═══"
  git status
  echo ""
  echo "═══ Current branch ═══"
  git branch -vv
  echo ""
  echo "═══ All branches ═══"
  git branch -a
  echo ""
  echo "═══ Remotes ═══"
  git remote -v
  echo ""
  echo "═══ Last 30 commits ═══"
  git log --oneline --graph --all --decorate -30
  echo ""
  echo "═══ Contributors ═══"
  git shortlog -sn --all | head -20
  echo ""
  echo "═══ Repo size ═══"
  du -sh .git
  echo ""
  echo "═══ .gitignore ═══"
  cat .gitignore
} > "$OUT/git/status.txt" 2>&1
ok "Git status"

{
  cd ~/h1-ai
  echo "═══ Uncommitted changes ═══"
  git diff --stat
  echo ""
  echo "═══ Staged changes ═══"
  git diff --cached --stat
  echo ""
  echo "═══ Untracked files ═══"
  git ls-files --others --exclude-standard | head -50
  echo ""
  echo "═══ Stashes ═══"
  git stash list
  echo ""
  echo "═══ Tags ═══"
  git tag -l | tail -20
  echo ""
  echo "═══ Recent activity (last 10 commits by date) ═══"
  git log --pretty=format:"%h | %ad | %an | %s" --date=short -10
} > "$OUT/git/changes.txt" 2>&1
ok "Git changes"

{
  cd ~/h1-ai
  echo "═══ Fetch remote state ═══"
  git fetch --all --prune 2>&1 | head -20
  echo ""
  echo "═══ Local vs Remote ═══"
  git status -sb
  echo ""
  echo "═══ Ahead/Behind ═══"
  git rev-list --left-right --count origin/main...HEAD 2>/dev/null || echo "لا يوجد origin/main"
  echo ""
  echo "═══ Large files in git ═══"
  git ls-files | xargs -I{} du -h {} 2>/dev/null | sort -hr | head -20
} > "$OUT/git/remote.txt" 2>&1
ok "Git remote"

# ───────────────────────────────────────────────────────────────
# 4. DOCKER
# ───────────────────────────────────────────────────────────────
step "[4/12] Docker"

{
  echo "═══ Version ═══"
  docker version
  echo ""
  echo "═══ Info ═══"
  docker info
  echo ""
  echo "═══ Containers (all) ═══"
  docker ps -a
  echo ""
  echo "═══ Images ═══"
  docker images
  echo ""
  echo "═══ Volumes ═══"
  docker volume ls
  echo ""
  echo "═══ Networks ═══"
  docker network ls
  echo ""
  echo "═══ Disk usage ═══"
  docker system df -v
} > "$OUT/docker/overview.txt" 2>&1
ok "Docker overview"

{
  for c in $(docker ps -a --format '{{.Names}}'); do
    echo "═══════════════════════════════════════════════════════════════"
    echo "CONTAINER: $c"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "─── Inspect (key fields) ───"
    docker inspect "$c" | python3 -c "
import sys, json
data = json.load(sys.stdin)[0]
print('Image:      ', data['Config'].get('Image'))
print('State:      ', data['State'].get('Status'))
print('Health:     ', data['State'].get('Health', {}).get('Status', 'N/A'))
print('Started:    ', data['State'].get('StartedAt'))
print('Restarts:   ', data['RestartCount'])
print('Ports:      ', data['NetworkSettings'].get('Ports'))
print('Command:    ', ' '.join(data['Config'].get('Cmd') or []))
print('Entrypoint: ', data['Config'].get('Entrypoint'))
print('WorkingDir: ', data['Config'].get('WorkingDir'))
"
    echo ""
    echo "─── Logs (last 50) ───"
    docker logs "$c" --tail 50 2>&1
    echo ""
    echo "─── Stats ───"
    docker stats "$c" --no-stream 2>&1
    echo ""
  done
} > "$OUT/docker/details.txt" 2>&1
ok "Docker details"

# ───────────────────────────────────────────────────────────────
# 5. DATABASE
# ───────────────────────────────────────────────────────────────
step "[5/12] Database"

{
  echo "═══ PostgreSQL version ═══"
  psql --version
  sudo -u postgres psql -c "SELECT version();" 2>&1
  echo ""
  echo "═══ Databases ═══"
  sudo -u postgres psql -c "\l" 2>&1
  echo ""
  echo "═══ Users ═══"
  sudo -u postgres psql -c "\du" 2>&1
  echo ""
  echo "═══ Tables in h1ai ═══"
  sudo -u postgres psql -d h1ai -c "\dt" 2>&1
  echo ""
  echo "═══ Tables size ═══"
  sudo -u postgres psql -d h1ai -c "
    SELECT schemaname, tablename,
           pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
    FROM pg_tables
    WHERE schemaname NOT IN ('pg_catalog','information_schema')
    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
    LIMIT 20;" 2>&1
  echo ""
  echo "═══ Connections ═══"
  sudo -u postgres psql -c "SELECT * FROM pg_stat_activity WHERE datname='h1ai';" 2>&1
  echo ""
  echo "═══ h1ai extensions ═══"
  sudo -u postgres psql -d h1ai -c "\dx" 2>&1
  echo ""
  echo "═══ Row counts (top 20 tables) ═══"
  sudo -u postgres psql -d h1ai -c "
    SELECT schemaname, relname, n_live_tup
    FROM pg_stat_user_tables
    ORDER BY n_live_tup DESC LIMIT 20;" 2>&1
} > "$OUT/db/postgres.txt" 2>&1
ok "PostgreSQL"

{
  echo "═══ Redis version ═══"
  redis-cli --version
  echo ""
  echo "═══ PING ═══"
  redis-cli -p 6379 ping 2>&1
  echo ""
  echo "═══ INFO ═══"
  redis-cli -p 6379 info 2>&1
  echo ""
  echo "═══ DBSIZE ═══"
  redis-cli -p 6379 dbsize 2>&1
  echo ""
  echo "═══ Keys sample ═══"
  redis-cli -p 6379 --scan --pattern '*' 2>&1 | head -30
  echo ""
  echo "═══ Slow log ═══"
  redis-cli -p 6379 slowlog get 10 2>&1
} > "$OUT/db/redis.txt" 2>&1
ok "Redis"

# ───────────────────────────────────────────────────────────────
# 6. NETWORK
# ───────────────────────────────────────────────────────────────
step "[6/12] Network"

{
  echo "═══ Interfaces ═══"
  ip -br addr
  echo ""
  echo "═══ Routes ═══"
  ip route
  echo ""
  echo "═══ DNS ═══"
  cat /etc/resolv.conf
  echo ""
  echo "═══ Listening ports ═══"
  sudo ss -tlnp
  echo ""
  echo "═══ Connections ═══"
  sudo ss -tnp
  echo ""
  echo "═══ UFW status ═══"
  sudo ufw status verbose
  echo ""
  echo "═══ iptables summary ═══"
  sudo iptables -L -n | head -50
} > "$OUT/network/overview.txt" 2>&1
ok "Network overview"

{
  echo "═══ Local API endpoints ═══"
  for port in 8000 3001 5432 6379 8200 8080 8888 9999; do
    code=$(curl -s -m 2 -o /dev/null -w "%{http_code}" "http://localhost:$port/" 2>/dev/null || echo "FAIL")
    printf "%-8s → %s\n" "$port" "$code"
  done
  echo ""
  echo "═══ Backend endpoints ═══"
  for path in / /health /docs /redoc /openapi.json /admin /admin/dashboard /login /v1/chat/help/admin /v1/products /v1/users /metrics; do
    code=$(curl -s -m 3 -o /dev/null -w "%{http_code}" "http://localhost:8000$path" 2>/dev/null || echo "FAIL")
    printf "%-35s → %s\n" "$path" "$code"
  done
  echo ""
  echo "═══ WhatsApp service ═══"
  for path in / /health /sessions /qr; do
    code=$(curl -s -m 3 -o /dev/null -w "%{http_code}" "http://localhost:3001$path" 2>/dev/null || echo "FAIL")
    printf "%-15s → %s\n" "$path" "$code"
  done
} > "$OUT/network/endpoints.txt" 2>&1
ok "Endpoints"

{
  echo "═══ Tailscale ═══"
  tailscale status 2>&1
  echo ""
  tailscale netcheck 2>&1 | head -30
  echo ""
  echo "═══ Cloudflared tunnel info ═══"
  docker logs h1ai-tunnel --tail 30 2>&1
} > "$OUT/network/tunnels.txt" 2>&1
ok "Tunnels"

# ───────────────────────────────────────────────────────────────
# 7. LOGS
# ───────────────────────────────────────────────────────────────
step "[7/12] Logs"

{
  for svc in h1ai.service h1ai-whatsapp.service h1ai-health.service h1ai-backup.service postgresql redis-server nginx tailscaled; do
    echo "═══════════════════════════════════════════════════════════════"
    echo "SERVICE: $svc"
    echo "═══════════════════════════════════════════════════════════════"
    systemctl status "$svc" --no-pager 2>&1 | head -20
    echo ""
    echo "─── Last 30 log entries ───"
    sudo journalctl -u "$svc" -n 30 --no-pager 2>&1
    echo ""
    echo "─── Errors (last 24h) ───"
    sudo journalctl -u "$svc" --since "24 hours ago" -p err --no-pager 2>&1 | tail -20
    echo ""
  done
} > "$OUT/logs/services.txt" 2>&1
ok "Service logs"

{
  echo "═══ System logs ═══"
  echo "─── syslog (last 100) ───"
  sudo tail -100 /var/log/syslog 2>&1
  echo ""
  echo "─── auth.log (last 50) ───"
  sudo tail -50 /var/log/auth.log 2>&1
  echo ""
  echo "─── kern.log (last 50) ───"
  sudo tail -50 /var/log/kern.log 2>&1
  echo ""
  echo "─── dmesg errors ───"
  sudo dmesg --level err,warn | tail -50
  echo ""
  echo "─── journal errors (last 24h) ───"
  sudo journalctl --since "24 hours ago" -p err --no-pager 2>&1 | tail -50
} > "$OUT/logs/system.txt" 2>&1
ok "System logs"

{
  echo "═══ Application logs ═══"
  for log in ~/h1-ai/backend/logs/*.log ~/h1-ai/whatsapp-service/*.log ~/h1-ai/logs/*.log /var/log/h1ai.log; do
    if [ -f "$log" ]; then
      echo "─── $log ───"
      echo "Size: $(du -h $log | cut -f1)"
      echo "Lines: $(wc -l < $log)"
      echo "Last modified: $(stat -c %y $log)"
      echo ""
      echo "Last 30 lines:"
      tail -30 "$log" 2>&1
      echo ""
      echo "Errors/warnings:"
      grep -iE "error|warn|fail|exception|traceback" "$log" 2>&1 | tail -20
      echo ""
      echo "═══════════════════════════════════════════════════════════════"
    fi
  done
} > "$OUT/logs/application.txt" 2>&1
ok "App logs"

# ───────────────────────────────────────────────────────────────
# 8. SECURITY
# ───────────────────────────────────────────────────────────────
step "[8/12] Security"

{
  echo "═══ Users with shells ═══"
  grep -E ":/bin/(ba)?sh$" /etc/passwd
  echo ""
  echo "═══ Sudo access ═══"
  sudo cat /etc/sudoers 2>&1
  sudo ls -la /etc/sudoers.d/ 2>&1
  for f in /etc/sudoers.d/*; do
    [ -f "$f" ] && echo "─── $f ───" && sudo cat "$f" 2>&1
  done
  echo ""
  echo "═══ SSH config ═══"
  sudo cat /etc/ssh/sshd_config 2>&1 | grep -v "^#" | grep -v "^$"
  echo ""
  echo "═══ SSH authorized keys ═══"
  for user_home in /home/* /root; do
    [ -f "$user_home/.ssh/authorized_keys" ] && echo "─── $user_home ───" && sudo cat "$user_home/.ssh/authorized_keys" 2>&1
  done
  echo ""
  echo "═══ Failed login attempts ═══"
  sudo lastb 2>&1 | head -20
  echo ""
  echo "═══ Recent logins ═══"
  last 2>&1 | head -20
} > "$OUT/security/users.txt" 2>&1
ok "Users & SSH"

{
  echo "═══ .env file permissions ═══"
  find ~/h1-ai -name ".env*" -exec ls -la {} \; 2>&1
  echo ""
  echo "═══ .secrets permissions ═══"
  ls -la ~/h1-ai/.secrets/ 2>&1
  echo ""
  echo "═══ Check for exposed secrets in git ═══"
  cd ~/h1-ai
  git log --all -p 2>/dev/null | grep -iE "api[_-]?key|password|secret|token|gsk_" | head -30
  echo ""
  echo "═══ Sensitive files with wrong perms ═══"
  find ~/h1-ai -type f \( -name "*.pem" -o -name "*.key" -o -name "*.env" -o -name "*.crt" -o -name "id_rsa*" \) -exec ls -la {} \; 2>&1
} > "$OUT/security/secrets.txt" 2>&1
ok "Secrets"

{
  echo "═══ Firewall ═══"
  sudo ufw status verbose
  echo ""
  echo "═══ Fail2ban ═══"
  sudo fail2ban-client status 2>&1
  for jail in sshd nginx-http-auth nginx-limit-req; do
    echo "─── jail: $jail ───"
    sudo fail2ban-client status "$jail" 2>&1
  done
  echo ""
  echo "═══ Suricata status ═══"
  sudo systemctl status suricata --no-pager 2>&1 | head -15
  echo ""
  echo "═══ SUID files ═══"
  find / -perm -4000 -type f 2>/dev/null | head -30
} > "$OUT/security/firewall.txt" 2>&1
ok "Firewall & fail2ban"

# ───────────────────────────────────────────────────────────────
# 9. ERRORS
# ───────────────────────────────────────────────────────────────
step "[9/12] Errors"

{
  echo "═══ Python import test ═══"
  cd ~/h1-ai/backend
  source ~/venvs/h1-ai-backend/bin/activate 2>/dev/null

  for module in main agents.tools agents.customer_agent core.orchestrator api.whatsapp_webhook knowledge.loader knowledge.engine db; do
    echo "─── import $module ───"
    python -c "import $module; print('OK')" 2>&1 | tail -20
    echo ""
  done

  echo "═══ Full OpenAPI generation ═══"
  python -c "
from main import app
schema = app.openapi()
print('OpenAPI OK:', len(schema.get('paths', {})), 'paths')
" 2>&1 | tail -30

} > "$OUT/errors/imports.txt" 2>&1
ok "Import tests"

{
  echo "═══ Backend errors ═══"
  sudo journalctl -u h1ai.service --since "24 hours ago" -p err --no-pager 2>&1 | tail -50
  echo ""
  echo "═══ WhatsApp errors ═══"
  sudo journalctl -u h1ai-whatsapp.service --since "24 hours ago" -p err --no-pager 2>&1 | tail -50
  echo ""
  echo "═══ OOM kills ═══"
  sudo dmesg | grep -i "killed process" 2>&1
  echo ""
  echo "═══ Failed services ═══"
  systemctl --failed --no-pager 2>&1
  echo ""
  echo "═══ Zombie processes ═══"
  ps aux | awk '$8 ~ /Z/ {print}' 2>&1
} > "$OUT/errors/service_errors.txt" 2>&1
ok "Service errors"

# ───────────────────────────────────────────────────────────────
# 10. PERFORMANCE
# ───────────────────────────────────────────────────────────────
step "[10/12] Performance"

{
  echo "═══ Top 20 processes by CPU ═══"
  ps aux --sort=-%cpu | head -21
  echo ""
  echo "═══ Top 20 processes by RAM ═══"
  ps aux --sort=-%mem | head -21
  echo ""
  echo "═══ Load average ═══"
  cat /proc/loadavg
  echo ""
  echo "═══ I/O stats ═══"
  iostat -x 1 2 2>&1 || echo "sysstat غير مثبت"
  echo ""
  echo "═══ Process count by user ═══"
  ps -eo user= | sort | uniq -c | sort -rn
} > "$OUT/performance/processes.txt" 2>&1
ok "Processes"

{
  echo "═══ Backend HTTP timing ═══"
  for i in 1 2 3 4 5; do
    curl -s -o /dev/null -w "Health #$i: %{http_code} (%{time_total}s)\n" http://localhost:8000/health
  done
  echo ""
  for path in /docs /openapi.json /admin/dashboard; do
    echo "─── $path ───"
    for i in 1 2 3; do
      curl -s -o /dev/null -w "  #$i: %{http_code} (%{time_total}s)\n" "http://localhost:8000$path"
    done
  done
  echo ""
  echo "═══ WhatsApp timing ═══"
  for i in 1 2 3; do
    curl -s -o /dev/null -w "Sessions #$i: %{http_code} (%{time_total}s)\n" http://localhost:3001/sessions
  done
} > "$OUT/performance/http_timing.txt" 2>&1
ok "HTTP timing"

# ───────────────────────────────────────────────────────────────
# 11. DEV TOOLS
# ───────────────────────────────────────────────────────────────
step "[11/12] Dev tools"

{
  echo "═══ Versions ═══"
  echo "Python:        $(python3 --version 2>&1)"
  echo "pip:           $(pip --version 2>&1)"
  echo "Node:          $(node --version 2>&1)"
  echo "npm:           $(npm --version 2>&1)"
  echo "Docker:        $(docker --version 2>&1)"
  echo "Docker Compose:$(docker compose version 2>&1)"
  echo "Git:           $(git --version 2>&1)"
  echo "Make:          $(make --version 2>&1 | head -1)"
  echo "curl:          $(curl --version 2>&1 | head -1)"
  echo "uvicorn:       $(~/.venvs/h1-ai-backend/bin/uvicorn --version 2>&1)"
  echo "alembic:       $(~/.venvs/h1-ai-backend/bin/alembic --version 2>&1)"
  echo "ruff:          $(~/.venvs/h1-ai-backend/bin/ruff --version 2>&1)"
  echo "black:         $(~/.venvs/h1-ai-backend/bin/black --version 2>&1)"
  echo "pytest:        $(~/.venvs/h1-ai-backend/bin/pytest --version 2>&1)"
  echo ""
  echo "═══ Venvs ═══"
  ls -la ~/venvs/ 2>&1
  for venv in ~/venvs/*/; do
    echo "─── $venv ───"
    du -sh "$venv" 2>&1
    "$venv/bin/python" --version 2>&1
  done
} > "$OUT/dev/versions.txt" 2>&1
ok "Dev versions"

# ───────────────────────────────────────────────────────────────
# 12. HEALTH CHECK
# ───────────────────────────────────────────────────────────────
step "[12/12] Health check"

{
  echo "═══ Services ═══"
  for svc in h1ai.service h1ai-whatsapp.service h1ai-health.service h1ai-backup.service h1ai-backup.timer postgresql redis-server tailscaled nginx suricata fail2ban; do
    status=$(systemctl is-active "$svc" 2>&1)
    enabled=$(systemctl is-enabled "$svc" 2>&1)
    printf "%-28s active=%-10s enabled=%s\n" "$svc" "$status" "$enabled"
  done
  echo ""
  echo "═══ Endpoints ═══"
  for url in "http://localhost:8000/health" "http://localhost:3001/health" "http://localhost:8000/docs"; do
    code=$(curl -s -m 3 -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "FAIL")
    printf "%-45s → %s\n" "$url" "$code"
  done
} > "$OUT/health/services.txt" 2>&1
ok "Services health"

# ───────────────────────────────────────────────────────────────
# تقرير مُجمَّع
# ───────────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  📊 توليد التقرير المُجمَّع"
echo "═══════════════════════════════════════════════════════════════"

{
  echo "╔═══════════════════════════════════════════════════════════════╗"
  echo "║  H1-AI Full Scan Report                                       ║"
  echo "║  Generated: $(date '+%Y-%m-%d %H:%M:%S')                          ║"
  echo "╚═══════════════════════════════════════════════════════════════╝"
  echo ""

  echo "═══ ملخص سريع ═══"
  echo "OS:      $(lsb_release -d 2>/dev/null | cut -f2)"
  echo "Kernel:  $(uname -r)"
  echo "Uptime:  $(uptime -p)"
  echo "CPU:     $(lscpu | grep 'Model name' | head -1 | cut -d: -f2 | xargs)"
  echo "Cores:   $(nproc)"
  echo "RAM:     $(free -h | awk '/^Mem:/ {print $2}')"
  echo "Disk /:  $(df -h / | awk 'NR==2 {print $2" total, "$4" free ("$5" used)"}')"
  echo ""

  echo "═══ الخدمات ═══"
  for svc in h1ai.service h1ai-whatsapp.service postgresql redis-server tailscaled; do
    printf "  %-28s %s\n" "$svc" "$(systemctl is-active $svc 2>&1)"
  done
  echo ""

  echo "═══ المشروع ═══"
  echo "  المسار:   ~/h1-ai"
  echo "  الحجم:    $(du -sh ~/h1-ai 2>/dev/null | cut -f1)"
  echo "  الملفات:  $(find ~/h1-ai -type f 2>/dev/null | grep -v '.git\|node_modules\|__pycache__' | wc -l)"
  echo ""

  echo "═══ Git ═══"
  cd ~/h1-ai
  echo "  Branch:    $(git branch --show-current 2>&1)"
  echo "  Commit:    $(git rev-parse --short HEAD 2>&1)"
  echo "  Status:    $(git status --porcelain 2>&1 | wc -l) تغييرات غير مُعتمد"
  echo ""

  echo "═══ الحجم الكلي ═══"
  echo "  Report dir: $OUT"
  echo "  Report size: $(du -sh $OUT 2>/dev/null | cut -f1)"
  echo ""

  echo "═══ الملفات المُنتَجة ═══"
  find "$OUT" -type f | sort | sed "s|$OUT/||"
} > "$OUT/REPORT.md" 2>&1

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${C_GREEN}✅ اكتمل الفحص الشامل${C_NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📁 التقرير في:"
echo "   $OUT"
echo ""
echo "📄 الملف الرئيسي:"
echo "   $OUT/REPORT.md"
echo ""
echo "📊 عرض الملخص:"
cat "$OUT/REPORT.md"
echo ""
