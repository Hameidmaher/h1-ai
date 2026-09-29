#!/bin/bash
# Live logs viewer
cd "$(dirname "${BASH_SOURCE[0]}")"

if [ ! -d "logs" ]; then
    echo "No logs yet. Run ./start.sh first"
    exit 1
fi

echo "═══════════════════════════════════════════════════════════"
echo "  📋 Live Logs (Ctrl+C to exit)"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Follow both logs with prefix
tail -f logs/backend.log logs/whatsapp.log 2>/dev/null | sed -u 's/^/  /'
