#!/usr/bin/env bash
pkill -f "node server.js" 2>/dev/null && echo "✅ أُوقف" || echo "⚠️  لم يكن يعمل"
