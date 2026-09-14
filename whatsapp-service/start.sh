#!/usr/bin/env bash
cd "$(dirname "$0")"

if [ ! -d "node_modules" ]; then
    echo "📦 تثبيت المكتبات..."
    npm install
fi

echo "🚀 تشغيل WhatsApp Service..."
node server.js
