#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 🗂️ H1-AI — Merge Project Files (Part 2)
# ═══════════════════════════════════════════════════════════════
set -e

H1AI="$HOME/h1-ai"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
log()  { echo -e "${BLUE}▶ $1${NC}"; }
ok()   { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }

echo "═══════════════════════════════════════════════════════════════"
echo "  🗂️  Merge Part 2 — الملفات المتبقية"
echo "═══════════════════════════════════════════════════════════════"

# ─── 1. نقل مجلدات audit الحقيقية (مع دمج إن كان الهدف فارغاً) ───
log "[1/4] معالجة audit dirs..."
for src in audit_report deep_audit full_audit project_audit; do
    if [ -d "$HOME/$src" ]; then
        SRC_COUNT=$(ls -A "$HOME/$src" 2>/dev/null | wc -l)
        DST="$H1AI/audit/$src"
        DST_COUNT=$(ls -A "$DST" 2>/dev/null | wc -l)

        if [ "$SRC_COUNT" -gt 0 ] && [ "$DST_COUNT" -eq 0 ]; then
            # الهدف فارغ → احذفه وحرّك الأصل
            rmdir "$DST" 2>/dev/null
            mv "$HOME/$src" "$H1AI/audit/"
            ok "$src ($SRC_COUNT ملف) → audit/"
        elif [ "$SRC_COUNT" -gt 0 ] && [ "$DST_COUNT" -gt 0 ]; then
            # كلاهما فيه محتوى → دمج
            cp -rn "$HOME/$src/"* "$DST/" 2>/dev/null || true
            warn "$src مدمج مع audit/$src (احتفظ بالأصل)"
        else
            rmdir "$HOME/$src" 2>/dev/null && ok "$src كان فارغاً وحُذف"
        fi
    fi
done

# ─── 2. تأمين الملفات الحساسة ───
log "[2/4] تأمين الملفات الحساسة..."
mkdir -p "$H1AI/.secrets"
chmod 700 "$H1AI/.secrets"

for f in .h1ai_admin_pass .h1ai_admin_user .h1ai_github_token \
         .h1ai_github_token.save .h1ai_old_tokens.txt; do
    if [ -f "$HOME/$f" ]; then
        mv "$HOME/$f" "$H1AI/.secrets/"
        chmod 600 "$H1AI/.secrets/$f"
        ok "$f → .secrets/"
    fi
done

if [ -d "$HOME/.h1ai-secrets" ]; then
    if [ ! -d "$H1AI/.secrets/legacy" ]; then
        mv "$HOME/.h1ai-secrets" "$H1AI/.secrets/legacy"
        chmod -R 700 "$H1AI/.secrets/legacy"
        ok ".h1ai-secrets → .secrets/legacy/"
    fi
fi

# ─── 3. نقل ~/scripts/backup-h1ai.sh ───
log "[3/4] نقل سكربتات خارجية..."
if [ -f "$HOME/scripts/backup-h1ai.sh" ]; then
    mkdir -p "$H1AI/scripts/external"
    mv "$HOME/scripts/backup-h1ai.sh" "$H1AI/scripts/external/"
    ok "backup-h1ai.sh → scripts/external/"
fi
[ -d "$HOME/scripts" ] && rmdir "$HOME/scripts" 2>/dev/null && ok "~/scripts حُذف (كان فارغاً)" || true

# ─── 4. حذف merge-project.sh ───
log "[4/4] تنظيف سكربت الدمج..."
if [ -f "$HOME/merge-project.sh" ]; then
    mkdir -p "$H1AI/scripts/fixes"
    mv "$HOME/merge-project.sh" "$H1AI/scripts/fixes/" 2>/dev/null
    ok "merge-project.sh → scripts/fixes/"
fi
[ -f "$HOME/merge-project-2.sh" ] && cp "$HOME/merge-project-2.sh" "$H1AI/scripts/fixes/" 2>/dev/null

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ اكتمل الدمج (الجزء 2)${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""

echo "🔍 المتبقي في ~/Home:"
ls -1 "$HOME" | grep -iE "h1|audit|deep|full|project|merge|\.h1ai" || echo "  لا شيء يخص المشروع ✅"
echo ""
echo "📁 الهيكل:"
echo "  ~/h1-ai/"
echo "  ├── .secrets/           ← ملفات حساسة (chmod 700)"
echo "  ├── audit/              ← كل التقارير"
echo "  ├── backups/            ← كل النسخ الاحتياطية"
echo "  ├── scripts/fixes/      ← سكربتات الإصلاح"
echo "  ├── scripts/external/   ← backup-h1ai.sh"
echo "  ├── mobile/backup/"
echo "  └── related/            ← فارغ (h1ai-analysis يُرك يدوياً)"
echo ""
echo "⚠️  h1ai-analysis يعمل من ~/h1ai-analysis — لا تحركه الآن"
echo ""
