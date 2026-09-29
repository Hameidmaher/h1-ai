#!/usr/bin/env python3
"""Seed 10 team members."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / "h1-ai" / "backend"))

from uuid import uuid4
from db import SessionLocal
from db.repositories import TeamRepository


TEAM_MEMBERS = [
    # 1. Senior Pharmacist (Prescriptions)
    {
        "id": str(uuid4()),
        "name": "Dr. Ahmed Mohamed",
        "name_ar": "د. أحمد محمد",
        "phone": "+201000000001",
        "email": "ahmed@h1-ai.com",
        "role": "pharmacist",
        "specialties": ["prescriptions", "interactions"],
        "shift": "morning",
        "max_concurrent": 15,
        "languages": ["ar", "en"],
    },
    # 2. Clinical Pharmacist (Interactions)
    {
        "id": str(uuid4()),
        "name": "Dr. Fatma Ali",
        "name_ar": "د. فاطمة علي",
        "phone": "+201000000002",
        "email": "fatma@h1-ai.com",
        "role": "pharmacist",
        "specialties": ["interactions", "drug_info"],
        "shift": "morning",
        "max_concurrent": 15,
        "languages": ["ar", "en"],
    },
    # 3. Inventory Pharmacist
    {
        "id": str(uuid4()),
        "name": "Dr. Mohamed Hassan",
        "name_ar": "د. محمد حسن",
        "phone": "+201000000003",
        "email": "mohamed@h1-ai.com",
        "role": "pharmacist",
        "specialties": ["inventory", "products"],
        "shift": "morning",
        "max_concurrent": 20,
        "languages": ["ar"],
    },
    # 4. Customer Service
    {
        "id": str(uuid4()),
        "name": "Sara Ibrahim",
        "name_ar": "سارة إبراهيم",
        "phone": "+201000000004",
        "email": "sara@h1-ai.com",
        "role": "customer_service",
        "specialties": ["general", "products"],
        "shift": "morning",
        "max_concurrent": 25,
        "languages": ["ar"],
    },
    # 5. Customer Service (Evening)
    {
        "id": str(uuid4()),
        "name": "Nour Abdelrahman",
        "name_ar": "نور عبدالرحمن",
        "phone": "+201000000005",
        "email": "nour@h1-ai.com",
        "role": "customer_service",
        "specialties": ["general", "complaints"],
        "shift": "evening",
        "max_concurrent": 25,
        "languages": ["ar"],
    },
    # 6. Evening Pharmacist
    {
        "id": str(uuid4()),
        "name": "Dr. Omar Khaled",
        "name_ar": "د. عمر خالد",
        "phone": "+201000000006",
        "email": "omar@h1-ai.com",
        "role": "pharmacist",
        "specialties": ["prescriptions", "general"],
        "shift": "evening",
        "max_concurrent": 15,
        "languages": ["ar", "en"],
    },
    # 7. Night Pharmacist
    {
        "id": str(uuid4()),
        "name": "Dr. Yasmine Said",
        "name_ar": "د. ياسمين سعيد",
        "phone": "+201000000007",
        "email": "yasmine@h1-ai.com",
        "role": "pharmacist",
        "specialties": ["interactions", "urgent"],
        "shift": "night",
        "max_concurrent": 20,
        "languages": ["ar", "en"],
    },
    # 8. Inventory Manager
    {
        "id": str(uuid4()),
        "name": "Khaled Mahmoud",
        "name_ar": "خالد محمود",
        "phone": "+201000000008",
        "email": "khaled@h1-ai.com",
        "role": "supervisor",
        "specialties": ["inventory", "suppliers"],
        "shift": "morning",
        "max_concurrent": 30,
        "languages": ["ar"],
    },
    # 9. Complaints Handler
    {
        "id": str(uuid4()),
        "name": "Mona Tarek",
        "name_ar": "منى طارق",
        "phone": "+201000000009",
        "email": "mona@h1-ai.com",
        "role": "customer_service",
        "specialties": ["complaints", "escalation"],
        "shift": "flexible",
        "max_concurrent": 20,
        "languages": ["ar", "en"],
    },
    # 10. Manager
    {
        "id": str(uuid4()),
        "name": "Dr. Hassan Ibrahim",
        "name_ar": "د. حسن إبراهيم",
        "phone": "+201000000010",
        "email": "hassan@h1-ai.com",
        "role": "manager",
        "specialties": ["prescriptions", "escalation", "approval"],
        "shift": "flexible",
        "max_concurrent": 10,
        "languages": ["ar", "en"],
    },
]


def main():
    print("═══════════════════════════════════════════════════")
    print("  Seeding 10 Team Members")
    print("═══════════════════════════════════════════════════")
    print()
    
    db = SessionLocal()
    try:
        repo = TeamRepository(db)
        
        # Check if already seeded
        existing = repo.count()
        if existing > 0:
            print(f"⚠️  Already have {existing} team members")
            print(f"   Skipping seed (use --force to override)")
            return
        
        added = 0
        for member in TEAM_MEMBERS:
            try:
                repo.create(**member)
                added += 1
                print(f"   ✅ Added: {member['name_ar']} ({member['role']}, {member['shift']})")
            except Exception as e:
                print(f"   ❌ Failed: {member['name']}: {e}")
        
        print()
        print(f"✅ Seeded {added} team members")
        print()
        
        stats = repo.stats()
        print(f"📊 Stats: {stats}")
        print()
        
        # Show by role
        from collections import Counter
        all_members = repo.list_all(active_only=False)
        roles = Counter(m.role for m in all_members)
        shifts = Counter(m.shift for m in all_members)
        print(f"By role:   {dict(roles)}")
        print(f"By shift:  {dict(shifts)}")
        
    finally:
        db.close()
    
    print()
    print("═══════════════════════════════════════════════════")
    print("  ✅ Done")
    print("═══════════════════════════════════════════════════")


if __name__ == "__main__":
    main()
