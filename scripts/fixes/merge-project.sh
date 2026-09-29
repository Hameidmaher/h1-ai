#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 🗂️ H1-AI — Merge Project Files
# ═══════════════════════════════════════════════════════════════
set -e

H1AI="$HOME/h1-ai"
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; NC='\033[0m'
log()  { echo -e "${BLUE}▶ $1${NC}"; }
ok()   { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
err()  { echo -e "${RED}❌ $1${NC}"; }

echo "═══════════════════════════════════════════════════════════════"
echo "  🗂️  H1-AI — Merge Project Files"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# ─── فحص أولي ───
if [ ! -d "$H1AI" ]; then
    err "$H1AI غير موجود!"
    exit 1
fi

# ─── فحص الملفات الغريبة ───
log "[0/6] فحص الملفات الغريبة..."
for f in "$HOME/threading" "$HOME/urllib.error"; do
    if [ -e "$f" ]; then
        echo ""
        echo "  🔍 $f:"
        file "$f" 2>/dev/null || true
        echo "  ─── أول 5 أسطر ───"
        head -5 "$f" 2>/dev/null || true
        echo "  ─── الحجم ───"
        du -h "$f" 2>/dev/null || true
        echo ""
    fi
done
read -p "  متابعة النقل؟ (y/N) " -n 1 -r
echo
[[ ! $REPLY =~ ^[Yy]$ ]] && exit 0

# ─── إنشاء مجلدات الوجهة ───
log "[1/6] إنشاء مجلدات الوجهة..."
mkdir -p "$H1AI"/{audit/{full_audit,deep_audit,audit_report,project_audit,archives,reports},backups,related,mobile/backup}
ok "تم"

# ─── نقل مجلدات audit ───
log "[2/6] نقل مجلدات audit..."
for src in full_audit deep_audit audit_report project_audit; do
    if [ -d "$HOME/$src" ]; then
        if [ ! -d "$H1AI/audit/$src" ]; then
            mv "$HOME/$src" "$H1AI/audit/"
            ok "$src → audit/"
        else
            warn "$src موجود بالفعل في audit/"
        fi
    fi
done

# ─── نقل backup dirs ───
log "[3/6] نقل النسخ الاحتياطية..."
for src in h1-ai.backup.20260927_100358 h1-ai.backup.20260927_100528; do
    if [ -d "$HOME/$src" ]; then
        DEST="$H1AI/backups/archive_${src#h1-ai.backup.}"
        if [ ! -d "$DEST" ]; then
            mv "$HOME/$src" "$DEST"
            ok "$src → backups/$(basename "$DEST")"
        else
            warn "$src موجود بالفعل"
        fi
    fi
done

for src in h1ai_backups_20260926 h1ai_cc_backup; do
    if [ -d "$HOME/$src" ]; then
        if [ ! -d "$H1AI/backups/$src" ]; then
            mv "$HOME/$src" "$H1AI/backups/"
            ok "$src → backups/"
        else
            warn "$src موجود بالفعل"
        fi
    fi
done

# ─── نقل h1-ai-analysis ───
log "[4/6] نقل المشاريع المرتبطة..."
if [ -d "$HOME/h1-ai-analysis" ]; then
    if [ ! -d "$H1AI/related/h1-ai-analysis" ]; then
        mv "$HOME/h1-ai-analysis" "$H1AI/related/"
        ok "h1-ai-analysis → related/"
    else
        warn "h1-ai-analysis موجود بالفعل"
    fi
fi

# ─── نقل ملفات audit reports ───
log "[5/6] نقل ملفات التقارير..."
for f in audit_report.tar.gz deep_audit.tar.gz full_audit.tar.gz project_audit.tar.gz; do
    [ -f "$HOME/$f" ] && mv "$HOME/$f" "$H1AI/audit/archives/" && ok "$f → audit/archives/"
done

for f in bt_deep_diagnostic.txt drivers_full_report.txt hardware_full_report.txt; do
    [ -f "$HOME/$f" ] && mv "$HOME/$f" "$H1AI/audit/reports/" && ok "$f → audit/reports/"
done

# ─── نقل install-fixes.sh ───
log "[6/6] نقل سكربتات الإصلاح..."
if [ -f "$HOME/install-fixes.sh" ]; then
    mkdir -p "$H1AI/scripts/fixes"
    mv "$HOME/install-fixes.sh" "$H1AI/scripts/fixes/"
    ok "install-fixes.sh → scripts/fixes/"
fi

if [ -f "$HOME/AndroidManifest.xml.bak" ]; then
    mv "$HOME/AndroidManifest.xml.bak" "$H1AI/mobile/backup/"
    ok "AndroidManifest.xml.bak → mobile/backup/"
fi

# ─── الملفات الغريبة (اختياري) ───
if [ -f "$HOME/threading" ] || [ -f "$HOME/urllib.error" ]; then
    mkdir -p "$H1AI/audit/odd_files"
    [ -f "$HOME/threading" ]    && mv "$HOME/threading"    "$H1AI/audit/odd_files/" && ok "threading → audit/odd_files/"
    [ -f "$HOME/urllib.error" ] && mv "$HOME/urllib.error" "$H1AI/audit/odd_files/" && ok "urllib.error → audit/odd_files/"
fi

# ═══════════════════════════════════════════════════════════════
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ اكتمل الدمج${NC}"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📁 الهيكل الجديد لـ ~/h1-ai:"
echo ""
du -sh "$H1AI"/* 2>/dev/null | sort -h | tail -20
echo ""
echo "🔍 المتبقي في ~/Home (يخص المشروع):"
ls -1 "$HOME" | grep -iE "h1|audit|deep|full|project" || echo "  لا شيء ✅"
echo ""
