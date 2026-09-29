#!/usr/bin/env python3
"""H1-AI — Expand products: 292 → 1000"""
import csv, random
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

DATA = Path.home() / "h1-ai" / "data"
CSV_PATH = DATA / "products.csv"

print("\n" + "=" * 60)
print("  📦 Expanding Products: 292 → 1000")
print("=" * 60 + "\n")

existing = list(csv.DictReader(open(CSV_PATH, encoding="utf-8")))
existing_codes = {r["ItemCode"] for r in existing}
print(f"📊 Current: {len(existing)}")

today = datetime.now()

# Brand database
BRANDS = {
    "Analgesic": [
        ("Panadol", 25, 80), ("Adol", 15, 40), ("Panadol Extra", 25, 50),
        ("Panadol Joint", 65, 95), ("Cataflam", 45, 75), ("Voltaren", 75, 110),
        ("Brufen", 35, 60), ("Celebrex", 120, 180), ("Arcoxia", 145, 210),
        ("Ponstan", 35, 55), ("Mobic", 95, 140), ("Feldene", 55, 85),
        ("Diclac", 28, 50), ("Olfen", 40, 70), ("Indocid", 38, 60),
        ("Ketorol", 65, 105), ("Naproxen", 42, 65), ("Aleve", 55, 90),
    ],
    "Antibiotic": [
        ("Augmentin", 90, 150), ("Amoxil", 30, 55), ("Hiconcil", 25, 50),
        ("E-Mox", 28, 55), ("Zithromax", 105, 160), ("Azomax", 85, 140),
        ("Klacid", 125, 190), ("Klaricid", 100, 160), ("Cipro", 75, 120),
        ("Ciprobay", 78, 120), ("Velosef", 55, 85), ("Keflex", 48, 75),
        ("Zinnat", 88, 135), ("Suprax", 98, 150), ("Tavanic", 135, 205),
        ("Flagyl", 42, 65), ("Rovamycin", 145, 220), ("Dalacin", 92, 140),
        ("Erythrocin", 58, 90), ("Vibramycin", 75, 115), ("Unasyn", 65, 100),
        ("Septrin", 35, 55), ("Bactrim", 28, 45), ("Minocin", 88, 135),
        ("Fucidin", 95, 145), ("Zyvox", 380, 550), ("Zerstat", 70, 115),
    ],
    "Vitamin": [
        ("Cebion", 25, 50), ("Redoxon", 55, 95), ("Vitacid C", 35, 65),
        ("Vidrop", 55, 90), ("Devarol", 65, 110), ("Calcitriol", 75, 120),
        ("Folic Acid", 15, 35), ("Folvite", 45, 85), ("Calcium Sandoz", 40, 75),
        ("Caltrate", 55, 95), ("Caltron", 45, 80), ("Iron Plus", 35, 65),
        ("Feroglobin", 65, 110), ("Sideral", 75, 125), ("Zinc Plus", 25, 50),
        ("Zinc Sulfate", 18, 40), ("Magnesium Plus", 35, 70), ("Mg Plus", 45, 80),
        ("Omega-3", 85, 150), ("Multivit", 55, 100), ("Pharmaton", 95, 165),
        ("StressTabs", 105, 180), ("Supradyn", 75, 125), ("Centrum", 125, 215),
        ("Vit B Complex", 45, 80), ("Neurobion", 85, 145), ("Neuroton", 95, 160),
        ("Collagen", 180, 300), ("Hyaluronic", 165, 280), ("Biotin", 95, 160),
        ("Glucosamine", 145, 240), ("CoQ10", 195, 320), ("L-Carnitine", 135, 225),
        ("Probiotics", 95, 160),
    ],
    "Gastrointestinal": [
        ("Losec", 85, 130), ("Antopral", 55, 95), ("Omez", 45, 80),
        ("Nexium", 68, 110), ("Pariet", 125, 190), ("Controloc", 115, 175),
        ("Zantac", 32, 55), ("Ranitidine", 25, 45), ("Gaviscon", 45, 75),
        ("Maalox", 38, 65), ("Mucaine", 52, 90), ("Colofac", 68, 110),
        ("Duspatalin", 95, 160), ("Debridat", 55, 90), ("Motilium", 42, 70),
        ("Domperidone", 35, 60), ("Primperan", 35, 60), ("Zofran", 145, 230),
        ("Iberogast", 88, 150), ("Duphalac", 42, 75), ("Fybogel", 45, 80),
        ("Movicol", 55, 95), ("Librax", 68, 115), ("Buscopan", 32, 55),
        ("Spasfon", 55, 90), ("Imodium", 22, 40), ("Antinal", 18, 35),
        ("Streptoquin", 45, 75),
    ],
    "Cardiovascular": [
        ("Concor", 52, 90), ("Bisoprolol", 40, 70), ("Tenormin", 48, 80),
        ("Atenolol", 35, 60), ("Lopressor", 52, 85), ("Metoprolol", 42, 70),
        ("Norvasc", 65, 110), ("Amlodipine", 42, 75), ("Zestril", 55, 95),
        ("Lisinopril", 38, 65), ("Renitec", 58, 100), ("Cozaar", 95, 160),
        ("Losartan", 65, 110), ("Diovan", 125, 205), ("Valsartan", 95, 160),
        ("Micardis", 135, 225), ("Aprovel", 145, 240), ("Atacand", 105, 175),
        ("Crestor", 195, 320), ("Lipitor", 85, 145), ("Zocor", 78, 130),
        ("Pravachol", 72, 120), ("Plavix", 145, 230), ("Clopidogrel", 95, 160),
        ("Efient", 165, 270), ("Lanoxin", 45, 75), ("Cordarone", 105, 175),
        ("Aldactone", 55, 95), ("Lasix", 32, 55), ("Furosemide", 22, 40),
        ("Capoten", 42, 70), ("Tritace", 68, 115), ("Adalat", 62, 105),
        ("Isoptin", 55, 90), ("Verapamil", 45, 75),
    ],
    "Diabetes": [
        ("Glucophage", 32, 55), ("Metformin", 25, 45), ("Amaryl", 65, 110),
        ("Glimepiride", 45, 80), ("Diamicron", 85, 145), ("Gliclazide", 65, 110),
        ("Novonorm", 125, 205), ("Repaglinide", 95, 160), ("Actos", 145, 230),
        ("Pioglitazone", 110, 180), ("Galvus", 195, 320), ("Januvia", 220, 360),
        ("Janumet", 245, 400), ("Forxiga", 215, 350), ("Jardiance", 235, 380),
        ("Lantus", 320, 500), ("NovoRapid", 295, 470), ("Humalog", 310, 490),
        ("Mixtard", 185, 300), ("Insulin", 150, 280),
    ],
    "Respiratory": [
        ("Ventolin", 85, 140), ("Salbutamol", 55, 95), ("Asthalin", 65, 110),
        ("Symbicort", 285, 450), ("Seretide", 295, 470), ("Singulair", 125, 200),
        ("Montelukast", 95, 160), ("Accolate", 185, 295), ("Atrovent", 95, 155),
        ("Spiriva", 380, 600), ("Bricanyl", 115, 185), ("Berodual", 125, 200),
        ("Pulmicort", 165, 265), ("Flixotide", 145, 230), ("Serevent", 195, 310),
        ("Combivent", 135, 220), ("Theo-Dur", 68, 115), ("Zaditen", 85, 145),
    ],
    "Antihistamine": [
        ("Claritin", 45, 75), ("Loratadine", 22, 45), ("Zyrtec", 42, 70),
        ("Cetirizine", 18, 40), ("Aerius", 68, 115), ("Desloratadine", 42, 75),
        ("Allegra", 65, 110), ("Telfast", 78, 130), ("Fexofenadine", 48, 85),
        ("Xyzal", 72, 120), ("Levocetirizine", 45, 80), ("Benadryl", 22, 40),
        ("Atarax", 38, 65), ("Phenergan", 32, 55), ("Nasonex", 125, 205),
        ("Flixonase", 105, 175), ("Rhinocort", 115, 195), ("Avamys", 135, 225),
    ],
    "OTC": [
        ("Panadol Cold", 32, 55), ("Theraflu", 45, 75), ("Coldrex", 38, 65),
        ("Otrivin", 52, 90), ("Vicks", 42, 70), ("Strepsils", 28, 50),
        ("Septolete", 32, 55), ("Sinutab", 45, 80), ("Actifed", 38, 65),
        ("Rhinathiol", 48, 85), ("Congestal", 22, 45), ("Listerine", 65, 110),
        ("Sensodyne", 78, 130), ("Colgate", 45, 80), ("Corsodyl", 85, 145),
        ("Bonjela", 45, 80),
    ],
    "Topical": [
        ("Lamisil", 85, 145), ("Canesten", 65, 110), ("Daktarin", 72, 120),
        ("Fucidin", 95, 160), ("Bactroban", 105, 175), ("Elocon", 115, 195),
        ("Dermovate", 125, 210), ("Locoid", 95, 160), ("Diproson", 88, 150),
        ("Protopic", 285, 470), ("Acnelyse", 65, 110), ("Differin", 145, 240),
        ("Benzac", 55, 90), ("Skinoren", 85, 145), ("Zovirax", 85, 145),
        ("Fenistil", 55, 95), ("Betadine", 42, 75), ("Hydrocortisone", 32, 60),
        ("Silver Sulfadiazine", 65, 110),
    ],
    "Cosmetic": [
        ("La Roche-Posay", 185, 320), ("Vichy", 220, 380), ("Bioderma", 195, 340),
        ("Avene", 165, 290), ("Eucerin", 245, 420), ("Nivea", 65, 110),
        ("Cetaphil", 125, 215), ("CeraVe", 145, 250), ("The Ordinary", 135, 235),
        ("Neutrogena", 155, 270), ("Loreal", 185, 320), ("Olay", 225, 390),
        ("Garnier", 85, 150), ("Ponds", 75, 130), ("Filorga", 380, 650),
    ],
    "Eye/Ear": [
        ("Systane", 95, 160), ("Refresh Plus", 85, 145), ("Visine", 45, 80),
        ("Maxitrol", 95, 160), ("Tobradex", 105, 175), ("Xalatan", 245, 420),
        ("Timoptic", 165, 280), ("Ciprofloxacin", 55, 95), ("Candibiotic", 78, 130),
        ("Otosporin", 85, 145), ("Polydexa", 95, 160), ("Sofradex", 105, 175),
    ],
    "Device": [
        ("Omron BP", 650, 1100), ("Omron HEM", 850, 1450), ("Accu-Chek", 420, 720),
        ("Accu-Chek Active", 520, 880), ("Omron Nebulizer", 850, 1450),
        ("Omron Compressor", 1250, 2100), ("Pulse Oximeter", 220, 380),
        ("Digital Thermometer", 85, 145), ("Infrared Thermometer", 285, 480),
        ("Ear Thermometer", 320, 550), ("Stethoscope", 450, 780),
        ("Nebulizer Mask", 45, 80), ("Glucose Strips", 185, 320),
        ("BP Cuff", 125, 215), ("Nebulizer Kit", 85, 145),
    ],
    "First Aid": [
        ("First Aid Kit", 385, 660), ("Elastic Bandage", 32, 55),
        ("Triangular Bandage", 28, 50), ("Cotton Wool", 22, 40),
        ("Medical Scissors", 45, 80), ("Tweezers", 35, 60),
        ("Cold Pack", 42, 75), ("Hot Water Bag", 65, 115),
        ("Povidone Iodine", 55, 95), ("Hydrogen Peroxide", 28, 50),
        ("Alcohol Swabs", 25, 45), ("Adhesive Tape", 18, 35),
        ("Face Mask", 35, 65), ("Medical Gloves", 45, 80),
    ],
    "Dermatology": [
        ("Topicrem", 145, 250), ("Ducray", 165, 290), ("Klorane", 155, 270),
        ("Uriage", 175, 310), ("Mustela", 185, 325), ("Bepanthen", 95, 165),
        ("Emolium", 145, 250),
    ],
    "Pediatric": [
        ("Baby Panadol", 32, 55), ("Calpol", 45, 80), ("Nurofen Kids", 55, 95),
        ("Baby Vit D", 45, 80), ("Aptamil", 285, 500), ("NAN", 265, 470),
        ("Pediasure", 320, 550), ("Similac", 295, 510),
        ("Baby Cough Syrup", 55, 95), ("Baby Saline", 35, 65),
    ],
}

target = 1000
current = len(existing)
needed = target - current

counter = 5000
added = 0

for category, brands in BRANDS.items():
    for brand_name, min_p, max_p in brands:
        if added >= needed:
            break

        counter += 1
        code = str(counter)
        if code in existing_codes:
            continue

        price = random.randint(min_p, max_p)
        stock = random.randint(30, 300)
        days = random.randint(180, 720)
        expiry = (today + timedelta(days=days)).strftime("%Y-%m-%d")

        dosages = ["100mg", "200mg", "250mg", "400mg", "500mg", "1g", "10mg", "20mg", "40mg"]
        packs = ["", "20 tabs", "30 tabs", "60 tabs", "100ml", "200ml", "cream 30g", "gel 50g"]

        dosage = random.choice(dosages)
        pack = random.choice(packs)
        name = f"{brand_name} {dosage}".strip() + (f" ({pack})" if pack else "")

        existing.append({
            "ItemCode": code,
            "ItemName": name[:200],
            "Category": category,
            "Price": f"{price}.00",
            "StockQty": str(stock),
            "ExpiryDate": expiry,
            "Description": f"{category} - {brand_name}",
        })
        existing_codes.add(code)
        added += 1

    if added >= needed:
        break

FIELDS = ["ItemCode", "ItemName", "Category", "Price", "StockQty", "ExpiryDate", "Description"]

with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(existing)

print()
print(f"  ✅ Added {added} products")
print(f"  ✅ Total: {current} → {len(existing)}")

cats = Counter(p["Category"] for p in existing)
print()
print("  Categories:")
for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
    print(f"     • {cat:25s} {count}")

print()
print("=" * 60)
print("  ✅ Products expanded!")
print("=" * 60)
