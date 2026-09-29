#!/usr/bin/env python3
"""Analyze current data state."""
import json
import csv
from pathlib import Path
from collections import Counter

DATA = Path.home() / "h1-ai" / "data"

def analyze_products():
    p = DATA / "products.csv"
    if not p.exists():
        return
    with open(p, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    
    print(f"\n📦 PRODUCTS ({len(rows)} total)")
    cats = Counter(r.get("Category", "?") for r in rows)
    print(f"   Categories ({len(cats)}):")
    for cat, cnt in cats.most_common(10):
        print(f"     {cat}: {cnt}")
    
    # Missing fields
    missing = sum(1 for r in rows if not r.get("Description"))
    print(f"   Missing description: {missing}")

def analyze_drugs():
    p = DATA / "drugs.json"
    if not p.exists():
        return
    data = json.load(open(p, encoding="utf-8"))
    drugs = data.get("drugs", {})
    
    print(f"\n💊 DRUGS ({len(drugs)} total)")
    classes = Counter(d.get("class", "?") for d in drugs.values())
    print(f"   Top classes ({len(classes)}):")
    for cls, cnt in classes.most_common(10):
        print(f"     {cls}: {cnt}")
    
    # Missing fields
    no_alias = sum(1 for d in drugs.values() if not d.get("aliases"))
    print(f"   No aliases: {no_alias}")

def analyze_interactions():
    p = DATA / "interactions.json"
    if not p.exists():
        return
    data = json.load(open(p, encoding="utf-8"))
    interactions = data.get("interactions", [])
    
    print(f"\n⚠️  INTERACTIONS ({len(interactions)} total)")
    sev = Counter(i.get("severity", "?") for i in interactions)
    print(f"   Severity:")
    for s, cnt in sev.items():
        print(f"     {s}: {cnt}")

def analyze_conditions():
    import yaml
    p = DATA / "medical_rules.yaml"
    if not p.exists():
        return
    data = yaml.safe_load(open(p, encoding="utf-8"))
    conditions = data.get("conditions", {})
    emergencies = data.get("emergencies", {})
    
    print(f"\n📋 CONDITIONS ({len(conditions)} total)")
    print(f"🚨 EMERGENCIES ({len(emergencies)} total):")
    for k in emergencies.keys():
        print(f"     - {k}")

def analyze_synonyms():
    p = DATA / "synonyms_ar.json"
    if not p.exists():
        return
    data = json.load(open(p, encoding="utf-8"))
    
    print(f"\n📚 SYNONYMS ({len(data)} entries)")
    for k in list(data.keys())[:5]:
        v = data[k]
        v_str = str(v)[:60]
        print(f"   {k} → {v_str}")

if __name__ == "__main__":
    print("═══════════════════════════════════════════════════")
    print("  Data Analysis — Current State")
    print("═══════════════════════════════════════════════════")
    analyze_products()
    analyze_drugs()
    analyze_interactions()
    analyze_conditions()
    analyze_synonyms()
    print("\n═══════════════════════════════════════════════════")
    print("  ✅ Analysis complete")
    print("═══════════════════════════════════════════════════")
