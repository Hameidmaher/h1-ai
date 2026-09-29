#!/usr/bin/env bash
cd "$(dirname "$0")"
echo "⚠️  هذا سيمسح الجلسة الحالية"
read -p "هل أنت متأكد؟ [y/N]: " confirm
if [ "$confirm" = "y" ]; then
    rm -rf sessions/*
    echo "✅ تم مسح الجلسة"
    echo "   شغّل start.sh وامسح QR Code جديد"
fi
