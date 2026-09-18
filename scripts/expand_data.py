#!/usr/bin/env python3
"""Expand medical data — drugs, interactions, conditions, emergencies, synonyms."""
import json
import yaml
from pathlib import Path
from datetime import datetime

DATA = Path.home() / "h1-ai" / "data"
BACKUP = DATA / f"backup_{datetime.now().strftime('%Y%m%d_%H%M')}"

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"   ✅ Saved: {path}")

def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_yaml(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
    print(f"   ✅ Saved: {path}")

# ═══════════════════════════════════════════════════════
# 1. EXPAND DRUGS
# ═══════════════════════════════════════════════════════
def expand_drugs():
    print("\n💊 Expanding drugs...")
    path = DATA / "drugs.json"
    data = load_json(path)
    drugs = data.get("drugs", {})
    before = len(drugs)
    
    # Top-up drug list (common generics)
    NEW_DRUGS = {
        # Antibiotics
        "amoxicillin": {"name_ar": "أموكسيسيلين", "class": "penicillin", "indications": ["infection"]},
        "azithromycin": {"name_ar": "أزيثرومايسين", "class": "macrolide", "indications": ["infection"]},
        "cephalexin": {"name_ar": "سيفاليكسين", "class": "cephalosporin", "indications": ["infection"]},
        "ciprofloxacin": {"name_ar": "سيبروفلوكساسين", "class": "fluoroquinolone", "indications": ["infection"]},
        "clarithromycin": {"name_ar": "كلاريثرومايسين", "class": "macrolide", "indications": ["infection"]},
        "doxycycline": {"name_ar": "دوكسيسيكلين", "class": "tetracycline", "indications": ["infection"]},
        "metronidazole": {"name_ar": "ميترونيدازول", "class": "nitroimidazole", "indications": ["infection", "parasite"]},
        "nitrofurantoin": {"name_ar": "نيتروفورانتوين", "class": "nitrofuran", "indications": ["uti"]},
        
        # Antifungals
        "fluconazole": {"name_ar": "فلوكونازول", "class": "azole", "indications": ["fungal"]},
        "ketoconazole": {"name_ar": "كيتوكونازول", "class": "azole", "indications": ["fungal"]},
        "terbinafine": {"name_ar": "تيربينافين", "class": "allylamine", "indications": ["fungal"]},
        
        # Antivirals
        "acyclovir": {"name_ar": "أسيكلوفير", "class": "antiviral", "indications": ["herpes"]},
        "oseltamivir": {"name_ar": "أوسيلتاميفير", "class": "antiviral", "indications": ["flu"]},
        
        # Cardiovascular
        "amlodipine": {"name_ar": "أملوديبين", "class": "ccb", "indications": ["hypertension"]},
        "nifedipine": {"name_ar": "نيفيديبين", "class": "ccb", "indications": ["hypertension"]},
        "verapamil": {"name_ar": "فيراباميل", "class": "ccb", "indications": ["hypertension", "arrhythmia"]},
        "diltiazem": {"name_ar": "ديلتيازيم", "class": "ccb", "indications": ["hypertension"]},
        "losartan": {"name_ar": "لوسارتان", "class": "arb", "indications": ["hypertension"]},
        "valsartan": {"name_ar": "فالسارتان", "class": "arb", "indications": ["hypertension"]},
        "candesartan": {"name_ar": "كانديسارتان", "class": "arb", "indications": ["hypertension"]},
        "hydrochlorothiazide": {"name_ar": "هيدروكلوروثيازيد", "class": "diuretic", "indications": ["hypertension"]},
        "furosemide": {"name_ar": "فوروسيميد", "class": "loop_diuretic", "indications": ["edema", "hypertension"]},
        "spironolactone": {"name_ar": "سبيرونولاكتون", "class": "k_sparing_diuretic", "indications": ["edema"]},
        "atorvastatin": {"name_ar": "أتورفاستاتين", "class": "statin", "indications": ["hyperlipidemia"]},
        "rosuvastatin": {"name_ar": "روزوفاستاتين", "class": "statin", "indications": ["hyperlipidemia"]},
        "simvastatin": {"name_ar": "سيمفاستاتين", "class": "statin", "indications": ["hyperlipidemia"]},
        "metoprolol": {"name_ar": "ميتوبرولول", "class": "beta_blocker", "indications": ["hypertension"]},
        "bisoprolol": {"name_ar": "بيسوبرولول", "class": "beta_blocker", "indications": ["hypertension"]},
        "carvedilol": {"name_ar": "كارفيديلول", "class": "beta_blocker", "indications": ["heart_failure"]},
        "digoxin": {"name_ar": "ديجوكسين", "class": "cardiac_glycoside", "indications": ["heart_failure"]},
        "warfarin": {"name_ar": "وارفارين", "class": "anticoagulant", "indications": ["dvt"]},
        "clopidogrel": {"name_ar": "كلوبيدوجريل", "class": "antiplatelet", "indications": ["acs"]},
        
        # GI
        "omeprazole": {"name_ar": "أوميبرازول", "class": "ppi", "indications": ["gerd", "ulcer"]},
        "pantoprazole": {"name_ar": "بانتوبرازول", "class": "ppi", "indications": ["gerd"]},
        "esomeprazole": {"name_ar": "إيزوميبرازول", "class": "ppi", "indications": ["gerd"]},
        "ranitidine": {"name_ar": "رانيتيدين", "class": "h2_blocker", "indications": ["gerd"]},
        "famotidine": {"name_ar": "فاموتيدين", "class": "h2_blocker", "indications": ["gerd"]},
        "metoclopramide": {"name_ar": "ميتوكلوبراميد", "class": "antiemetic", "indications": ["nausea"]},
        "ondansetron": {"name_ar": "أوندانسيترون", "class": "antiemetic", "indications": ["nausea"]},
        "loperamide": {"name_ar": "لوبيراميد", "class": "antidiarrheal", "indications": ["diarrhea"]},
        "bisacodyl": {"name_ar": "بيساكوديل", "class": "laxative", "indications": ["constipation"]},
        "lactulose": {"name_ar": "لاكتولوز", "class": "laxative", "indications": ["constipation"]},
        
        # Diabetes
        "insulin_glargine": {"name_ar": "إنسولين جلارجين", "class": "insulin", "indications": ["diabetes_type1", "diabetes_type2"]},
        "insulin_aspart": {"name_ar": "إنسولين أسبارت", "class": "insulin", "indications": ["diabetes_type1", "diabetes_type2"]},
        "pioglitazone": {"name_ar": "بيوجليتازون", "class": "tzd", "indications": ["diabetes_type2"]},
        "sitagliptin": {"name_ar": "سيتاجليبتين", "class": "dpp4", "indications": ["diabetes_type2"]},
        "empagliflozin": {"name_ar": "إمباجليفلوزين", "class": "sglt2", "indications": ["diabetes_type2", "heart_failure"]},
        
        # Respiratory
        "albuterol": {"name_ar": "ألبوتيرول", "class": "saba", "indications": ["asthma"]},
        "budesonide": {"name_ar": "بوديسونيد", "class": "ics", "indications": ["asthma"]},
        "fluticasone": {"name_ar": "فلوتيكاسون", "class": "ics", "indications": ["asthma", "allergy"]},
        "beclomethasone": {"name_ar": "بيكلوميثازون", "class": "ics", "indications": ["asthma"]},
        "cetirizine": {"name_ar": "سيتيريزين", "class": "antihistamine", "indications": ["allergy"]},
        "loratadine": {"name_ar": "لوراتادين", "class": "antihistamine", "indications": ["allergy"]},
        "fexofenadine": {"name_ar": "فيكسوفينادين", "class": "antihistamine", "indications": ["allergy"]},
        "chlorpheniramine": {"name_ar": "كلورفينيرامين", "class": "antihistamine", "indications": ["allergy"]},
        "diphenhydramine": {"name_ar": "ديفينهيدرامين", "class": "antihistamine", "indications": ["allergy", "insomnia"]},
        
        # Pain / Anti-inflammatory
        "ibuprofen": {"name_ar": "إيبوبروفين", "class": "nsaid", "indications": ["pain", "inflammation"]},
        "naproxen": {"name_ar": "نابروكسين", "class": "nsaid", "indications": ["pain", "inflammation"]},
        "diclofenac": {"name_ar": "ديكلوفيناك", "class": "nsaid", "indications": ["pain", "inflammation"]},
        "celecoxib": {"name_ar": "سيليكوكسيب", "class": "coxib", "indications": ["pain", "arthritis"]},
        "aspirin": {"name_ar": "أسبرين", "class": "nsaid", "indications": ["pain", "acs"]},
        "tramadol": {"name_ar": "ترامادول", "class": "opioid", "indications": ["pain"]},
        "codeine": {"name_ar": "كودايين", "class": "opioid", "indications": ["pain", "cough"]},
        "morphine": {"name_ar": "مورفين", "class": "opioid", "indications": ["severe_pain"]},
        
        # Psychiatry / Neuro
        "citalopram": {"name_ar": "سيتالوبرام", "class": "ssri", "indications": ["depression"]},
        "fluvoxamine": {"name_ar": "فلوفوكسامين", "class": "ssri", "indications": ["ocd"]},
        "amitriptyline": {"name_ar": "أميتريبتيلين", "class": "tca", "indications": ["depression", "neuropathy"]},
        "nortriptyline": {"name_ar": "نورتريبتيلين", "class": "tca", "indications": ["depression"]},
        "haloperidol": {"name_ar": "هالوبيريدول", "class": "antipsychotic", "indications": ["schizophrenia"]},
        "aripiprazole": {"name_ar": "أريبيبرازول", "class": "antipsychotic", "indications": ["schizophrenia", "bipolar"]},
        "lithium": {"name_ar": "ليثيوم", "class": "mood_stabilizer", "indications": ["bipolar"]},
        "phenytoin": {"name_ar": "فينيتوين", "class": "antiepileptic", "indications": ["epilepsy"]},
        "topiramate": {"name_ar": "توبيراميت", "class": "antiepileptic", "indications": ["epilepsy", "migraine"]},
        "donepezil": {"name_ar": "دونيبيزيل", "class": "cholinesterase", "indications": ["alzheimer"]},
        "memantine": {"name_ar": "ميمانتين", "class": "nmda", "indications": ["alzheimer"]},
        "levodopa": {"name_ar": "ليفودوبا", "class": "dopamine", "indications": ["parkinson"]},
        
        # Hormones
        "estradiol": {"name_ar": "إستراديول", "class": "estrogen", "indications": ["hrt"]},
        "progesterone": {"name_ar": "بروجستيرون", "class": "progestin", "indications": ["hrt"]},
        "testosterone": {"name_ar": "تستوستيرون", "class": "androgen", "indications": ["hrt"]},
        "levonorgestrel": {"name_ar": "ليفونورجيستريل", "class": "progestin", "indications": ["contraception"]},
        "metformin": {"name_ar": "ميتفورمين", "class": "biguanide", "indications": ["diabetes_type2"]},
        "methimazole": {"name_ar": "ميثيمازول", "class": "antithyroid", "indications": ["hyperthyroidism"]},
        
        # Vitamins / Supplements
        "vitamin_d3": {"name_ar": "فيتامين د٣", "class": "vitamin", "indications": ["deficiency"]},
        "vitamin_b12": {"name_ar": "فيتامين ب١٢", "class": "vitamin", "indications": ["deficiency", "anemia"]},
        "folic_acid": {"name_ar": "حمض الفوليك", "class": "vitamin", "indications": ["pregnancy", "anemia"]},
        "iron_sulfate": {"name_ar": "كبريتات الحديد", "class": "mineral", "indications": ["anemia"]},
        "calcium_carbonate": {"name_ar": "كربونات الكالسيوم", "class": "mineral", "indications": ["deficiency"]},
        "magnesium": {"name_ar": "مغنيسيوم", "class": "mineral", "indications": ["deficiency"]},
        "zinc": {"name_ar": "زنك", "class": "mineral", "indications": ["deficiency"]},
        "omega3": {"name_ar": "أوميغا ٣", "class": "supplement", "indications": ["cardiovascular"]},
        
        # Urology
        "tamsulosin": {"name_ar": "تامسولوسين", "class": "alpha_blocker", "indications": ["bph"]},
        "finasteride": {"name_ar": "فيناستيريد", "class": "5ari", "indications": ["bph", "hair_loss"]},
        "sildenafil": {"name_ar": "سيلدينافيل", "class": "pde5", "indications": ["ed"]},
        "tadalafil": {"name_ar": "تادالافيل", "class": "pde5", "indications": ["ed", "bph"]},
        "oxybutynin": {"name_ar": "أوكسيبيوتينين", "class": "anticholinergic", "indications": ["overactive_bladder"]},
        
        # Dermatology
        "hydrocortisone": {"name_ar": "هيدروكورتيزون", "class": "corticosteroid", "indications": ["dermatitis"]},
        "betamethasone": {"name_ar": "بيتاميثازون", "class": "corticosteroid", "indications": ["dermatitis"]},
        "clotrimazole": {"name_ar": "كلوتريمازول", "class": "azole", "indications": ["fungal"]},
        "mupirocin": {"name_ar": "موبيروسين", "class": "antibiotic", "indications": ["skin_infection"]},
        "isotretinoin": {"name_ar": "أيزوتريتينوين", "class": "retinoid", "indications": ["acne"]},
        "benzoyl_peroxide": {"name_ar": "بنزويل بيروكسيد", "class": "keratolytic", "indications": ["acne"]},
        "tretinoin": {"name_ar": "تريتينوين", "class": "retinoid", "indications": ["acne", "aging"]},
    }
    
    added = 0
    for key, info in NEW_DRUGS.items():
        if key not in drugs:
            drugs[key] = {
                "name_ar": info.get("name_ar", key),
                "name_en": key.replace("_", " ").title(),
                "aliases": [],
                "class": info.get("class", "unknown"),
                "indications": info.get("indications", []),
                "safe_pregnancy": False,
                "safe_children": False,
            }
            added += 1
    
    data["drugs"] = drugs
    data["version"] = "4.0"
    data["updated_at"] = datetime.now().isoformat()
    save_json(path, data)
    
    print(f"   Before: {before}")
    print(f"   Added: {added}")
    print(f"   After: {len(drugs)}")

# ═══════════════════════════════════════════════════════
# 2. EXPAND INTERACTIONS
# ═══════════════════════════════════════════════════════
def expand_interactions():
    print("\n⚠️  Expanding interactions...")
    path = DATA / "interactions.json"
    data = load_json(path)
    interactions = data.get("interactions", [])
    before = len(interactions)
    
    # Common drug interactions
    NEW_INTERACTIONS = [
        # Anticoagulants
        {"drug1": "warfarin", "drug2": "aspirin", "severity": "major",
         "effect": "زيادة خطر النزيف", "action": "تجنب الجمع أو مراقبة INR"},
        {"drug1": "warfarin", "drug2": "ibuprofen", "severity": "major",
         "effect": "زيادة خطر النزيف", "action": "استخدم paracetamol بدلاً"},
        {"drug1": "warfarin", "drug2": "ciprofloxacin", "severity": "major",
         "effect": "زيادة تأثير الوارفارين", "action": "تقليل الجرعة + مراقبة INR"},
        {"drug1": "warfarin", "drug2": "metronidazole", "severity": "major",
         "effect": "زيادة تأثير الوارفارين", "action": "تجنب"},
        {"drug1": "warfarin", "drug2": "fluconazole", "severity": "major",
         "effect": "زيادة تأثير الوارفارين", "action": "مراقبة INR"},
        
        # Diabetes
        {"drug1": "metformin", "drug2": "contrast_media", "severity": "major",
         "effect": "خطر الحماض اللبني", "action": "إيقاف قبل الفحص 48 ساعة"},
        
        # SSRIs
        {"drug1": "sertraline", "drug2": "tramadol", "severity": "major",
         "effect": "متلازمة السيروتونين", "action": "تجنب"},
        {"drug1": "fluoxetine", "drug2": "tramadol", "severity": "major",
         "effect": "متلازمة السيروتونين", "action": "تجنب"},
        {"drug1": "sertraline", "drug2": "maoi", "severity": "major",
         "effect": "متلازمة السيروتونين", "action": "تجنب تماماً"},
        {"drug1": "sertraline", "drug2": "aspirin", "severity": "moderate",
         "effect": "زيادة خطر النزيف", "action": "مراقبة"},
        
        # Statins
        {"drug1": "simvastatin", "drug2": "clarithromycin", "severity": "major",
         "effect": "زيادة خطر الإعتلال العضلي", "action": "إيقاف الستاتين مؤقتاً"},
        {"drug1": "simvastatin", "drug2": "itraconazole", "severity": "major",
         "effect": "زيادة خطر الإعتلال العضلي", "action": "تجنب"},
        {"drug1": "atorvastatin", "drug2": "clarithromycin", "severity": "moderate",
         "effect": "زيادة تركيز الستاتين", "action": "تقليل الجرعة"},
        
        # Antibiotics
        {"drug1": "ciprofloxacin", "drug2": "calcium_carbonate", "severity": "moderate",
         "effect": "انخفاض امتصاص السيبروفلوكساسين", "action": "افصل بينهم ساعتين"},
        {"drug1": "tetracycline", "drug2": "calcium_carbonate", "severity": "moderate",
         "effect": "انخفاض الامتصاص", "action": "افصل بينهم ساعتين"},
        {"drug1": "doxycycline", "drug2": "iron_sulfate", "severity": "moderate",
         "effect": "انخفاض الامتصاص", "action": "افصل بينهم ساعتين"},
        
        # Cardiovascular
        {"drug1": "lisinopril", "drug2": "spironolactone", "severity": "major",
         "effect": "ارتفاع البوتاسيوم", "action": "مراقبة البوتاسيوم"},
        {"drug1": "metoprolol", "drug2": "verapamil", "severity": "major",
         "effect": "بطء القلب الشديد", "action": "تجنب"},
        {"drug1": "digoxin", "drug2": "amiodarone", "severity": "major",
         "effect": "زيادة تركيز الديجوكسين", "action": "تقليل الجرعة 50%"},
        {"drug1": "digoxin", "drug2": "furosemide", "severity": "moderate",
         "effect": "نقص البوتاسيوم", "action": "تعويض البوتاسيوم"},
        
        # Analgesics
        {"drug1": "ibuprofen", "drug2": "aspirin", "severity": "moderate",
         "effect": "زيادة خطر النزيف", "action": "تجنب الجمع"},
        {"drug1": "ibuprofen", "drug2": "lisinopril", "severity": "moderate",
         "effect": "انخفاض تأثير الضغط", "action": "مراقبة"},
        {"drug1": "ibuprofen", "drug2": "furosemide", "severity": "moderate",
         "effect": "انخفاض تأثير المدر", "action": "مراقبة"},
        {"drug1": "aspirin", "drug2": "methotrexate", "severity": "major",
         "effect": "زيادة سمية الميثوتريكسات", "action": "تجنب"},
        
        # CNS
        {"drug1": "diazepam", "drug2": "morphine", "severity": "major",
         "effect": "تثبيط الجهاز التنفسي", "action": "تجنب"},
        {"drug1": "alprazolam", "drug2": "alcohol", "severity": "major",
         "effect": "تثبيط الجهاز العصبي", "action": "تجنب"},
        {"drug1": "diazepam", "drug2": "tramadol", "severity": "moderate",
         "effect": "تثبيط CNS", "action": "مراقبة"},
        
        # PPIs
        {"drug1": "omeprazole", "drug2": "clopidogrel", "severity": "major",
         "effect": "انخفاض تأثير الكلوبيدوجريل", "action": "استخدم pantoprazole بدلاً"},
        
        # Hormones
        {"drug1": "levothyroxine", "drug2": "calcium_carbonate", "severity": "moderate",
         "effect": "انخفاض امتصاص الثيروكسين", "action": "افصل 4 ساعات"},
        {"drug1": "levothyroxine", "drug2": "iron_sulfate", "severity": "moderate",
         "effect": "انخفاض الامتصاص", "action": "افصل 4 ساعات"},
        {"drug1": "levothyroxine", "drug2": "omeprazole", "severity": "moderate",
         "effect": "انخفاض الامتصاص", "action": "مراقبة TSH"},
        
        # Respiratory
        {"drug1": "albuterol", "drug2": "metoprolol", "severity": "moderate",
         "effect": "تضاد التأثير", "action": "استخدم β1-selective"},
        
        # Antifungals
        {"drug1": "ketoconazole", "drug2": "omeprazole", "severity": "moderate",
         "effect": "انخفاض امتصاص الكيتوكونازول", "action": "استخدم شراب مع حمض"},
        
        # Additional major
        {"drug1": "phenytoin", "drug2": "warfarin", "severity": "major",
         "effect": "تغيرات متقلبة في INR", "action": "مراقبة لصيقة"},
        {"drug1": "carbamazepine", "drug2": "warfarin", "severity": "major",
         "effect": "انخفاض تأثير الوارفارين", "action": "زيادة الجرعة"},
        {"drug1": "rifampin", "drug2": "warfarin", "severity": "major",
         "effect": "انخفاض تأثير الوارفارين", "action": "زيادة الجرعة"},
        {"drug1": "amlodipine", "drug2": "simvastatin", "severity": "moderate",
         "effect": "زيادة تركيز السمفاستاتين", "action": "تقليل الجرعة"},
        {"drug1": "colchicine", "drug2": "clarithromycin", "severity": "major",
         "effect": "سمية الكولشيسين", "action": "تجنب"},
        {"drug1": "allopurinol", "drug2": "azathioprine", "severity": "major",
         "effect": "سمية نقية للدم", "action": "تقليل الجرعة 75%"},
        {"drug1": "methotrexate", "drug2": "trimethoprim", "severity": "major",
         "effect": "سمية نقية للدم", "action": "تجنب"},
        {"drug1": "ssri", "drug2": "nsaid", "severity": "moderate",
         "effect": "خطر النزيف GI", "action": "أضف PPI"},
    ]
    
    # Dedupe existing
    existing_pairs = {(i["drug1"], i["drug2"]) for i in interactions}
    existing_pairs |= {(i["drug2"], i["drug1"]) for i in interactions}
    
    added = 0
    for new_int in NEW_INTERACTIONS:
        pair = (new_int["drug1"], new_int["drug2"])
        if pair not in existing_pairs:
            interactions.append(new_int)
            existing_pairs.add(pair)
            added += 1
    
    data["interactions"] = interactions
    data["version"] = "3.0"
    data["updated_at"] = datetime.now().isoformat()
    save_json(path, data)
    
    print(f"   Before: {before}")
    print(f"   Added: {added}")
    print(f"   After: {len(interactions)}")

# ═══════════════════════════════════════════════════════
# 3. EXPAND EMERGENCIES
# ═══════════════════════════════════════════════════════
def expand_emergencies():
    print("\n🚨 Expanding emergencies...")
    path = DATA / "medical_rules.yaml"
    data = load_yaml(path)
    
    emergencies = data.get("emergencies", {})
    before = len(emergencies)
    
    NEW_EMERGENCIES = {
        "chest_pain": {
            "keywords": {
                "ar": ["ألم في الصدر", "ألم بالصدر", "وجع في الصدر", "ضغط على الصدر",
                       "ألم شديد في الصدر", "ألم في القلب"],
                "en": ["chest pain", "chest pressure", "heart pain"]
            },
            "message": "🚨 ألم في الصدر قد يكون علامة على نوبة قلبية. اتصل بالإسعاف فوراً!",
            "emergency_number": "123",
        },
        "difficulty_breathing": {
            "keywords": {
                "ar": ["صعوبة في التنفس", "مش قادر أتنفس", "ضيق في التنفس",
                       "أزمة ربو", "اختناق"],
                "en": ["difficulty breathing", "can't breathe", "shortness of breath"]
            },
            "message": "🚨 صعوبة في التنفس حالة طارئة. اطلب المساعدة الطبية فوراً!",
            "emergency_number": "123",
        },
        "severe_bleeding": {
            "keywords": {
                "ar": ["نزيف حاد", "نزيف شديد", "دم كتير", "جروح عميقة",
                       "نزيف مش بيتوقف"],
                "en": ["severe bleeding", "heavy bleeding", "can't stop bleeding"]
            },
            "message": "🚨 نزيف حاد يحتاج إسعاف فوري!",
            "emergency_number": "123",
        },
        "loss_of_consciousness": {
            "keywords": {
                "ar": ["فقدان الوعي", "أغمى عليه", "مغمى عليه", "مش حاسس بنفسه",
                       "غاب عن الوعي"],
                "en": ["loss of consciousness", "fainted", "unconscious"]
            },
            "message": "🚨 فقدان الوعي حالة طارئة! اتصل بالإسعاف فوراً!",
            "emergency_number": "123",
        },
        "stroke_symptoms": {
            "keywords": {
                "ar": ["جلطة", "جلطة دماغية", "شلل مفاجئ", "تنميل في الوجه",
                       "مش قادر أتكلم", "تشنجات"],
                "en": ["stroke", "sudden paralysis", "can't speak"]
            },
            "message": "🚨 أعراض جلطة دماغية! الوقت عامل حاسم — اتصل بالإسعاف فوراً!",
            "emergency_number": "123",
        },
        "severe_allergic": {
            "keywords": {
                "ar": ["حساسية شديدة", "تورم في الوجه", "تورم في الحلق",
                       "صعوبة في البلع", "طفح جلدي منتشر"],
                "en": ["severe allergy", "anaphylaxis", "face swelling", "throat swelling"]
            },
            "message": "🚨 حساسية شديدة قد تكون قاتلة! اتصل بالإسعاف فوراً!",
            "emergency_number": "123",
        },
        "poisoning": {
            "keywords": {
                "ar": ["تسمم", "سم", "بلع مادة سامة", "جرعة زائدة",
                       "أخذ أدوية كتير"],
                "en": ["poisoning", "overdose", "swallowed poison"]
            },
            "message": "🚨 تسمم أو جرعة زائدة! اتصل بمركز السموم فوراً!",
            "emergency_number": "123",
        },
        "severe_burns": {
            "keywords": {
                "ar": ["حرق شديد", "حرق كبير", "حرق واسع", "حرق من الدرجة الثالثة"],
                "en": ["severe burns", "third degree burns", "extensive burns"]
            },
            "message": "🚨 حروق شديدة تحتاج علاج طارئ!",
            "emergency_number": "123",
        },
        "severe_head_injury": {
            "keywords": {
                "ar": ["إصابة في الرأس", "ضربة على الرأس", "نزيف من الرأس",
                       "فقدان وعي بعد إصابة"],
                "en": ["head injury", "head trauma", "bleeding from head"]
            },
            "message": "🚨 إصابة في الرأس قد تكون خطيرة! اتصل بالإسعاف فوراً!",
            "emergency_number": "123",
        },
        "seizure": {
            "keywords": {
                "ar": ["تشنجات", "صرع", "نوبة صرع", "تشنج مفاجئ"],
                "en": ["seizure", "convulsion", "epileptic attack"]
            },
            "message": "🚨 نوبة صرع أو تشنج! اتصل بالإسعاف!",
            "emergency_number": "123",
        },
        "high_fever_children": {
            "keywords": {
                "ar": ["حرارة عالية لطفل", "حمى شديدة", "سخونة عالية",
                       "تشنجات حرارية"],
                "en": ["high fever child", "severe fever", "febrile seizure"]
            },
            "message": "🚨 حرارة عالية جداً لطفل! اذهب للطوارئ فوراً!",
            "emergency_number": "123",
        },
        "suicidal_thoughts": {
            "keywords": {
                "ar": ["أفكار انتحارية", "عايز أموت", "مش عايز أعيش",
                       "هأذي نفسي"],
                "en": ["suicidal", "want to die", "end my life"]
            },
            "message": "🚨 أنت مش لوحدك. اتصل بخط الدعم النفسي فوراً!",
            "emergency_number": "08008880700",
        },
        "pregnancy_bleeding": {
            "keywords": {
                "ar": ["نزيف حمل", "نزيف حامل", "ألم شديد في الحمل",
                       "إجهاض"],
                "en": ["pregnancy bleeding", "miscarriage", "severe pregnancy pain"]
            },
            "message": "🚨 نزيف الحمل حالة طارئة! اذهبي للطوارئ فوراً!",
            "emergency_number": "123",
        },
        "severe_abdominal_pain": {
            "keywords": {
                "ar": ["ألم شديد في البطن", "ألم حاد في البطن", "مغص شديد",
                       "ألم في المعدة شديد"],
                "en": ["severe abdominal pain", "acute abdomen", "severe stomach pain"]
            },
            "message": "🚨 ألم شديد في البطن قد يحتاج جراحة! اذهب للطوارئ!",
            "emergency_number": "123",
        },
        "eye_injury": {
            "keywords": {
                "ar": ["إصابة في العين", "دخل حاجة في العين", "مادة كاوية في العين",
                       "فقدان الرؤية المفاجئ"],
                "en": ["eye injury", "chemical in eye", "sudden vision loss"]
            },
            "message": "🚨 إصابة في العين! اذهب للطوارئ فوراً!",
            "emergency_number": "123",
        },
        "severe_dehydration": {
            "keywords": {
                "ar": ["جفاف شديد", "مش قادر أشرب", "قيء مستمر", "إسهال شديد"],
                "en": ["severe dehydration", "continuous vomiting", "severe diarrhea"]
            },
            "message": "🚨 جفاف شديد! يحتاج سوائل وريدية فوراً!",
            "emergency_number": "123",
        },
    }
    
    for key, info in NEW_EMERGENCIES.items():
        if key not in emergencies:
            emergencies[key] = info
    
    data["emergencies"] = emergencies
    save_yaml(path, data)
    
    print(f"   Before: {before}")
    print(f"   Added: {len(NEW_EMERGENCIES)}")
    print(f"   After: {len(emergencies)}")

# ═══════════════════════════════════════════════════════
# 4. EXPAND SYNONYMS
# ═══════════════════════════════════════════════════════
def expand_synonyms():
    print("\n📚 Expanding synonyms...")
    path = DATA / "synonyms_ar.json"
    data = load_json(path)
    before = len(data)
    
    NEW_SYNONYMS = {
        # Pain
        "صداع": ["صداع", "وجع راس", "ألم في الرأس", "headache", "صداع نصفي"],
        "ألم": ["ألم", "وجع", "مغص", "pain", "وجعان"],
        "حرارة": ["حرارة", "سخونة", "حمى", "fever", "حرارة عالية"],
        "برد": ["برد", "زكام", "رشح", "cold", "flu", "إنفلونزا"],
        "كحة": ["كحة", "سعال", "كح", "cough", "كحة جافة", "كحة ببلغم"],
        "التهاب الحلق": ["التهاب الحلق", "ألم الحلق", "وجع الزور", "sore throat"],
        "إسهال": ["إسهال", "نزلة معوية", "diarrhea", "إسهال شديد"],
        "قيء": ["قيء", "ترجيع", "استفراغ", "vomiting", "ترجيع مستمر"],
        "إمساك": ["إمساك", "قبض", "constipation", "مش قادر أدخل الحمام"],
        "غازات": ["غازات", "انتفاخ", "نفخة", "gas", "bloating"],
        "حموضة": ["حموضة", "حرقة في المعدة", "حرقان", "heartburn", "acid reflux"],
        "حساسية": ["حساسية", "أليرجي", "allergy", "طفح جلدي", "هرش"],
        "أرق": ["أرق", "صعوبة في النوم", "insomnia", "مش قادر أنام"],
        "قلق": ["قلق", "توتر", "anxiety", "خوف", "وسواس"],
        "اكتئاب": ["اكتئاب", "حزن", "depression", "مزاج سيء", "ضيق"],
        "سكر": ["سكر", "سكري", "diabetes", "سكر الدم", "نسبة السكر"],
        "ضغط": ["ضغط", "ضغط الدم", "hypertension", "blood pressure"],
        "كوليسترول": ["كوليسترول", "دهون", "cholesterol", "lipid"],
        "غدة": ["غدة", "غدة درقية", "thyroid", "الغدة"],
        "فيتامين": ["فيتامين", "vitamin", "فيتامينات", "مكملات"],
        "مناعة": ["مناعة", "immunity", "تقوية المناعة", "immune"],
        "وزن": ["وزن", "تخسيس", "weight", "رجيم", "دايت", "نحافة"],
        "شعر": ["شعر", "hair", "تساقط الشعر", "hair loss"],
        "بشرة": ["بشرة", "جلد", "skin", "حبوب", "acne", "حساسية جلدية"],
        "عظام": ["عظام", "مفاصل", "bones", "joints", "روماتيزم", "التهاب مفاصل"],
        "عضلات": ["عضلات", "muscles", "شد عضلي", "وجع عضلات"],
        "عين": ["عين", "eyes", "التهاب العين", "جفاف العين"],
        "أذن": ["أذن", "ear", "التهاب الأذن", "وجع الأذن"],
        "أنف": ["أنف", "nose", "انسداد الأنف", "حساسية الأنف"],
        "أسنان": ["أسنان", "teeth", "وجع الأسنان", "التهاب اللثة"],
    }
    
    added = 0
    for key, values in NEW_SYNONYMS.items():
        if key not in data:
            data[key] = values
            added += 1
    
    save_json(path, data)
    
    print(f"   Before: {before}")
    print(f"   Added: {added}")
    print(f"   After: {len(data)}")

# ═══════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════
if __name__ == "__main__":
    print("═══════════════════════════════════════════════════")
    print("  Expanding Medical Data")
    print("═══════════════════════════════════════════════════")
    
    # Create backup
    BACKUP.mkdir(exist_ok=True)
    for f in ["drugs.json", "interactions.json", "medical_rules.yaml", "synonyms_ar.json"]:
        src = DATA / f
        if src.exists():
            import shutil
            shutil.copy2(src, BACKUP / f)
    print(f"\n✅ Backup created: {BACKUP}\n")
    
    expand_drugs()
    expand_interactions()
    expand_emergencies()
    expand_synonyms()
    
    print("\n═══════════════════════════════════════════════════")
    print("  ✅ Expansion complete")
    print("═══════════════════════════════════════════════════")
