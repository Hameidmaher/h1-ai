#!/bin/bash
# ═══════════════════════════════════════════════════════════
# H1-AI — Test Script
# ═══════════════════════════════════════════════════════════

H1AI_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "═══════════════════════════════════════════════════════════"
echo "  🧪 H1-AI Tests"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Test 1: Health
echo -e "${BLUE}▶ Test 1: Backend Health${NC}"
curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null && echo -e "${GREEN}✅${NC}" || echo -e "${RED}❌${NC}"
echo ""

# Test 2: Customer
echo -e "${BLUE}▶ Test 2: Customer Message${NC}"
curl -s -X POST http://localhost:8000/webhook/v2/incoming \
    -H "Content-Type: application/json" \
    -d '{"phone": "+201111111111", "message": "عايز بديل للباراسيتامول", "name": "Test Customer"}' \
    | python3 -m json.tool 2>/dev/null | head -20
echo ""

# Test 3: Urgent
echo -e "${BLUE}▶ Test 3: Urgent Message${NC}"
curl -s -X POST http://localhost:8000/webhook/v2/incoming \
    -H "Content-Type: application/json" \
    -d '{"phone": "+201111111112", "message": "عندي ألم في الصدر", "name": "Test Urgent"}' \
    | python3 -m json.tool 2>/dev/null | head -20
echo ""

# Test 4: Spam
echo -e "${BLUE}▶ Test 4: Spam Message${NC}"
curl -s -X POST http://localhost:8000/webhook/v2/incoming \
    -H "Content-Type: application/json" \
    -d '{"phone": "+201111111113", "message": "Click here to buy now! Free money!", "name": "Test Spam"}' \
    | python3 -m json.tool 2>/dev/null | head -20
echo ""

# Test 5: DB Stats
echo -e "${BLUE}▶ Test 5: DB Stats${NC}"
cd "$H1AI_DIR/backend" && . .venv/bin/activate && python3 << 'ENDPY'
from db import SessionLocal
from db.repositories import MessageRepository, ReportRepository, TeamRepository
db = SessionLocal()
try:
    print(f"📨 Messages: {MessageRepository(db).stats(24)}")
    print(f"📋 Reports:  {ReportRepository(db).stats()}")
    print(f"👥 Team:     {TeamRepository(db).stats()}")
finally:
    db.close()
ENDPY

echo ""
echo "═══════════════════════════════════════════════════════════"
echo -e "  ${GREEN}✅ Tests complete${NC}"
echo "═══════════════════════════════════════════════════════════"
