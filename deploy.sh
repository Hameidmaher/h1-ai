#!/bin/bash
# Deploy to Railway

echo "🚀 Deploying to Railway..."
echo ""

# Check git status
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Uncommitted changes. Commit first."
    exit 1
fi

# Push to main
git push origin main

echo ""
echo "✅ Pushed! Railway will auto-deploy."
echo ""
echo "📊 Check status:"
echo "   https://railway.app/dashboard"
echo ""
echo "🌐 Your app will be live at:"
echo "   https://h1-ai-production.up.railway.app"

