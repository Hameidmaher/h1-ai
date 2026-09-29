#!/usr/bin/env python3
"""Products Part 2: 598 → 1000"""
import csv, random
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

CSV_PATH = Path.home() / "h1-ai" / "data" / "products.csv"
print("\n📦 Products Part 2: 598 → 1000\n")

existing = list(csv.DictReader(open(CSV_PATH, encoding="utf-8")))
existing_codes = {r["ItemCode"] for r in existing}
print(f"📊 Current: {len(existing)}")
today = datetime.now()

CATALOG = {
    "Sports Nutrition": [
        ("Whey Protein", 450, 850), ("Mass Gainer", 650, 1200),
        ("BCAA", 280, 500), ("Creatine", 220, 400),
        ("Pre-Workout", 350, 650), ("L-Glutamine", 180, 320),
        ("Beta Alanine", 150, 280), ("Casein Protein", 550, 950),
        ("Multivitamin Sport", 185, 340), ("Electrolytes", 125, 240),
        ("EAA", 250, 450), ("CLA", 195, 350),
        ("Carnitine Plus", 220, 400), ("ZMA", 165, 300),
        ("Taurine", 95, 180), ("Protein Bar", 55, 110),
        ("Protein Shake", 85, 165), ("Energy Gel", 45, 90),
        ("Isotonic Drink", 55, 110), ("Recovery Drink", 95, 185),
    ],
    "Maternity": [
        ("Prenatal Vitamins", 145, 280), ("Femibion 1", 185, 350),
        ("Femibion 2", 195, 370), ("Pregnacare Plus", 165, 320),
        ("Elevit", 195, 380), ("Omega Mom", 155, 300),
        ("Folic Plus", 85, 165), ("Iron Mom", 95, 185),
        ("Calcium Mom", 75, 145), ("DHA Mom", 185, 350),
        ("Maternity Belt", 245, 450), ("Nursing Pads", 65, 130),
        ("Stretch Mark Cream", 145, 280), ("Breast Pump", 850, 1500),
    ],
    "Baby Care": [
        ("Baby Lotion", 85, 165), ("Baby Shampoo", 65, 130),
        ("Baby Oil", 75, 145), ("Baby Powder", 55, 110),
        ("Baby Cream", 95, 185), ("Diaper Rash Cream", 105, 200),
        ("Baby Wipes", 45, 90), ("Baby Sunscreen", 155, 300),
        ("Baby Vit D", 55, 110), ("Baby Colic Drops", 85, 165),
        ("Baby Paracetamol", 45, 90), ("Baby Saline", 35, 70),
        ("Nasal Aspirator", 65, 130), ("Baby Thermometer", 185, 350),
        ("Baby Nail Clipper", 45, 90), ("Baby Brush Set", 55, 110),
        ("Baby Bottle", 85, 165), ("Pacifier", 35, 70),
        ("Baby Carrier", 450, 850), ("Baby Monitor", 850, 1500),
    ],
    "Personal Care": [
        ("Antiperspirant", 65, 130), ("Deodorant Spray", 55, 110),
        ("Hand Sanitizer", 35, 70), ("Body Lotion", 95, 185),
        ("Body Wash", 75, 145), ("Shampoo", 85, 165),
        ("Conditioner", 95, 185), ("Hair Oil", 105, 200),
        ("Hair Serum", 185, 350), ("Face Wash", 95, 185),
        ("Face Cream", 145, 280), ("Face Serum", 245, 450),
        ("Sunscreen Facial", 195, 370), ("Lip Balm", 45, 90),
        ("Razor", 85, 165), ("Shaving Cream", 75, 145),
        ("Toothbrush Electric", 320, 620), ("Water Flosser", 450, 880),
    ],
    "Medical Devices": [
        ("Wheelchair", 1800, 3500), ("Crutches", 320, 620),
        ("Walker", 550, 1000), ("Knee Support", 185, 350),
        ("Ankle Support", 145, 280), ("Wrist Support", 125, 240),
        ("Back Support", 245, 450), ("Cervical Collar", 195, 370),
        ("Compression Socks", 185, 350), ("Heating Pad", 245, 450),
        ("TENS Unit", 650, 1200), ("Massage Gun", 850, 1500),
        ("Vaporizer", 420, 780), ("Humidifier", 550, 1000),
        ("Air Purifier", 1250, 2200), ("Nebulizer Plus", 950, 1650),
        ("Blood Pressure Cuff", 185, 350), ("Glucose Meter Plus", 650, 1200),
    ],
    "Diagnostics": [
        ("Pregnancy Test", 45, 90), ("Ovulation Test", 85, 165),
        ("COVID Antigen Test", 65, 130), ("Blood Pressure Strips", 85, 165),
        ("Cholesterol Test", 245, 450), ("Uric Acid Test", 195, 370),
        ("Urine Test Strips", 125, 240), ("Ketone Test", 145, 280),
        ("Hemoglobin Meter", 650, 1200), ("INR Meter", 1850, 3500),
        ("Strep Test", 185, 350), ("H Pylori Test", 245, 450),
        ("Hepatitis Test", 195, 370), ("HIV Test", 245, 450),
    ],
    "Gastrointestinal Plus": [
        ("H2 Blocker", 45, 90), ("Probiotic Sachet", 65, 130),
        ("ORS Sachet", 15, 35), ("Antiemetic Syrup", 55, 110),
        ("Laxative Drops", 75, 145), ("Antispasmodic Plus", 95, 185),
        ("Digestive Enzymes", 125, 240), ("Simethicone Drops", 85, 165),
        ("Bile Salts", 145, 280), ("Colon Cleanse", 185, 350),
    ],
    "Cardiovascular Plus": [
        ("CoQ10 Plus 200", 285, 520), ("Omega Cardio", 185, 350),
        ("Garlic Extract", 95, 185), ("Red Yeast Rice", 165, 320),
        ("Hawthorn Berry", 145, 280), ("Nattokinase", 245, 450),
        ("L-Arginine 1000", 165, 320), ("Vitamin K2 MK7", 195, 370),
    ],
    "Diabetes Plus": [
        ("Sugar-Free Sweetener", 65, 130), ("Diabetic Socks", 125, 240),
        ("Diabetic Foot Cream", 145, 280), ("Glucose Tablets", 45, 90),
        ("Insulin Cooler", 450, 850), ("Insulin Pen Needles", 85, 165),
        ("Lancets", 45, 90), ("Continuous Monitor", 1850, 3500),
        ("Diabetic Meal", 85, 165), ("Sugar-Free Chocolate", 55, 110),
    ],
    "Dermatology Plus": [
        ("Acne Patches", 95, 185), ("Salicylic Acid 2%", 85, 165),
        ("Benzoyl 10%", 75, 145), ("Retinol 0.5%", 185, 350),
        ("Azelaic Acid 20%", 245, 450), ("Vitamin C Serum", 285, 520),
        ("Hyaluronic Serum", 245, 450), ("Niacinamide 10%", 165, 320),
        ("Sunscreen Gel", 185, 350), ("Micellar Water", 85, 165),
        ("Sheet Mask", 45, 90), ("Eye Patches", 95, 185),
    ],
    "Eye Care": [
        ("Eye Mask Warm", 185, 350), ("Eye Mask Cold", 145, 280),
        ("Lid Wipes", 85, 165), ("Eye Lubricant Gel", 125, 240),
        ("Contact Lens Solution", 95, 185), ("Contact Lens Case", 45, 90),
    ],
    "First Aid Plus": [
        ("Burn Gel", 65, 130), ("Burn Dressing", 95, 185),
        ("Emergency Blanket", 55, 110), ("Trauma Kit", 850, 1500),
        ("CPR Face Shield", 45, 90), ("Splint", 245, 450),
        ("Instant Ice Pack", 45, 90), ("Instant Heat Pack", 55, 110),
    ],
}

target = 1000
needed = target - len(existing)
counter = 6000
added = 0

for category, brands in CATALOG.items():
    for brand_name, min_p, max_p in brands:
        if added >= needed: break
        counter += 1
        code = str(counter)
        if code in existing_codes: continue

        price = random.randint(min_p, max_p)
        stock = random.randint(20, 200)
        days = random.randint(240, 720)
        expiry = (today + timedelta(days=days)).strftime("%Y-%m-%d")

        existing.append({
            "ItemCode": code, "ItemName": brand_name[:200],
            "Category": category, "Price": f"{price}.00",
            "StockQty": str(stock), "ExpiryDate": expiry,
            "Description": f"{category} - {brand_name}",
        })
        existing_codes.add(code)
        added += 1
    if added >= needed: break

with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["ItemCode","ItemName","Category","Price","StockQty","ExpiryDate","Description"])
    w.writeheader()
    w.writerows(existing)

print(f"\n  ✅ Added {added} products")
print(f"  ✅ Total: {len(existing)}")
print()
