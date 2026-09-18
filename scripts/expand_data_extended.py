#!/usr/bin/env python3
"""Extended data expansion — big batch."""
import json
import yaml
import csv
from pathlib import Path
from datetime import datetime

DATA = Path.home() / "h1-ai" / "data"

def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)

def save_yaml(path, data):
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


# ═══════════════════════════════════════════════════════
# 1. EXTENDED DRUGS (target: 600+)
# ═══════════════════════════════════════════════════════
def extend_drugs():
    print("\n💊 Extending drugs...")
    path = DATA / "drugs.json"
    data = load_json(path)
    drugs = data.get("drugs", {})
    before = len(drugs)
    
    NEW_DRUGS = {
        # More antibiotics
        "amoxicillin_clavulanate": {"name_ar": "أموكسيسيلين/كلافولانيك", "class": "penicillin", "indications": ["infection"]},
        "ampicillin": {"name_ar": "أمبيسيلين", "class": "penicillin", "indications": ["infection"]},
        "benzylpenicillin": {"name_ar": "بنزيل بنسلين", "class": "penicillin", "indications": ["infection"]},
        "cefazolin": {"name_ar": "سيفازولين", "class": "cephalosporin", "indications": ["infection"]},
        "cefixime": {"name_ar": "سيفيكسيم", "class": "cephalosporin", "indications": ["infection"]},
        "ceftriaxone": {"name_ar": "سيفترياكسون", "class": "cephalosporin", "indications": ["infection"]},
        "cefuroxime": {"name_ar": "سيفيوروكسيم", "class": "cephalosporin", "indications": ["infection"]},
        "clindamycin": {"name_ar": "كليندامايسين", "class": "lincosamide", "indications": ["infection"]},
        "erythromycin": {"name_ar": "إريثرومايسين", "class": "macrolide", "indications": ["infection"]},
        "gentamicin": {"name_ar": "جنتاميسين", "class": "aminoglycoside", "indications": ["infection"]},
        "levofloxacin": {"name_ar": "ليفوفلوكساسين", "class": "fluoroquinolone", "indications": ["infection"]},
        "linezolid": {"name_ar": "لينيزوليد", "class": "oxazolidinone", "indications": ["infection"]},
        "minocycline": {"name_ar": "مينوسيكلين", "class": "tetracycline", "indications": ["infection", "acne"]},
        "moxifloxacin": {"name_ar": "موكسيفلوكساسين", "class": "fluoroquinolone", "indications": ["infection"]},
        "penicillin_v": {"name_ar": "بنسلين في", "class": "penicillin", "indications": ["infection"]},
        "piperacillin_tazobactam": {"name_ar": "بيبراسيلين/تازوباكتام", "class": "penicillin", "indications": ["infection"]},
        "rifampin": {"name_ar": "ريفامبين", "class": "rifamycin", "indications": ["tuberculosis"]},
        "sulfamethoxazole_trimethoprim": {"name_ar": "سلفاميثوكسازول/تريميثوبريم", "class": "sulfonamide", "indications": ["uti"]},
        "tobramycin": {"name_ar": "توبراميسين", "class": "aminoglycoside", "indications": ["infection"]},
        "vancomycin": {"name_ar": "فانكومايسين", "class": "glycopeptide", "indications": ["infection"]},
        
        # More antivirals
        "entecavir": {"name_ar": "إنتيكافير", "class": "antiviral", "indications": ["hepatitis_b"]},
        "ganciclovir": {"name_ar": "جانجيكلوفير", "class": "antiviral", "indications": ["cmv"]},
        "ribavirin": {"name_ar": "ريبافيرين", "class": "antiviral", "indications": ["hepatitis_c"]},
        "tenofovir": {"name_ar": "تينوفوفير", "class": "antiviral", "indications": ["hiv", "hepatitis_b"]},
        "zidovudine": {"name_ar": "زيدوفودين", "class": "antiviral", "indications": ["hiv"]},
        
        # More antifungals
        "amphotericin_b": {"name_ar": "أمفوتيريسين ب", "class": "polyene", "indications": ["fungal"]},
        "caspofungin": {"name_ar": "كاسبوفنجين", "class": "echinocandin", "indications": ["fungal"]},
        "griseofulvin": {"name_ar": "جريزيوفولفين", "class": "antifungal", "indications": ["fungal"]},
        "itraconazole": {"name_ar": "إيتراكونازول", "class": "azole", "indications": ["fungal"]},
        "nystatin": {"name_ar": "نيستاتين", "class": "polyene", "indications": ["candida"]},
        "posaconazole": {"name_ar": "بوساكونازول", "class": "azole", "indications": ["fungal"]},
        "voriconazole": {"name_ar": "فوريكونازول", "class": "azole", "indications": ["fungal"]},
        
        # More cardiovascular
        "amiodarone": {"name_ar": "أميودارون", "class": "antiarrhythmic", "indications": ["arrhythmia"]},
        "atenolol": {"name_ar": "أتينولول", "class": "beta_blocker", "indications": ["hypertension"]},
        "bumetanide": {"name_ar": "بوميتانيد", "class": "loop_diuretic", "indications": ["edema"]},
        "captopril": {"name_ar": "كابتوبريل", "class": "ace_inhibitor", "indications": ["hypertension"]},
        "clonidine": {"name_ar": "كلونيدين", "class": "alpha_agonist", "indications": ["hypertension"]},
        "doxazosin": {"name_ar": "دوكسازوسين", "class": "alpha_blocker", "indications": ["bph", "hypertension"]},
        "enalapril": {"name_ar": "إنالابريل", "class": "ace_inhibitor", "indications": ["hypertension", "heart_failure"]},
        "eplerenone": {"name_ar": "إبليرينون", "class": "k_sparing_diuretic", "indications": ["heart_failure"]},
        "felodipine": {"name_ar": "فيلوديبين", "class": "ccb", "indications": ["hypertension"]},
        "flecainide": {"name_ar": "فليكاينيد", "class": "antiarrhythmic", "indications": ["arrhythmia"]},
        "hydralazine": {"name_ar": "هيدرالازين", "class": "vasodilator", "indications": ["hypertension"]},
        "isosorbide": {"name_ar": "إيزوسوربيد", "class": "nitrate", "indications": ["angina"]},
        "ivabradine": {"name_ar": "إيفابرادين", "class": "if_inhibitor", "indications": ["heart_failure"]},
        "labetalol": {"name_ar": "لابيتالول", "class": "beta_blocker", "indications": ["hypertension"]},
        "methyldopa": {"name_ar": "ميثيلدوبا", "class": "alpha_agonist", "indications": ["hypertension_pregnancy"]},
        "minoxidil": {"name_ar": "مينوكسيديل", "class": "vasodilator", "indications": ["hypertension", "hair_loss"]},
        "nicardipine": {"name_ar": "نيكارديبين", "class": "ccb", "indications": ["hypertension"]},
        "perindopril": {"name_ar": "بيريندوبريل", "class": "ace_inhibitor", "indications": ["hypertension"]},
        "prazosin": {"name_ar": "برازوسين", "class": "alpha_blocker", "indications": ["bph", "ptsd"]},
        "propafenone": {"name_ar": "بروبافينون", "class": "antiarrhythmic", "indications": ["arrhythmia"]},
        "quinidine": {"name_ar": "كينيدين", "class": "antiarrhythmic", "indications": ["arrhythmia"]},
        "ramipril": {"name_ar": "راميبريل", "class": "ace_inhibitor", "indications": ["hypertension"]},
        "sacubitril_valsartan": {"name_ar": "ساكوبيتريل/فالسارتان", "class": "arni", "indications": ["heart_failure"]},
        "sotalol": {"name_ar": "سوتالول", "class": "antiarrhythmic", "indications": ["arrhythmia"]},
        "telmisartan": {"name_ar": "تلميسارتان", "class": "arb", "indications": ["hypertension"]},
        "torsemide": {"name_ar": "تورسيميد", "class": "loop_diuretic", "indications": ["edema"]},
        
        # More GI
        "aluminum_hydroxide": {"name_ar": "هيدروكسيد الألومنيوم", "class": "antacid", "indications": ["gerd"]},
        "bismuth_subsalicylate": {"name_ar": "بزموت سبساليسيلات", "class": "antidiarrheal", "indications": ["diarrhea"]},
        "dicyclomine": {"name_ar": "ديسيكلومين", "class": "antispasmodic", "indications": ["ibs"]},
        "docusate": {"name_ar": "دوكوسات", "class": "stool_softener", "indications": ["constipation"]},
        "domperidone": {"name_ar": "دومبيريدون", "class": "antiemetic", "indications": ["nausea"]},
        "hyoscyamine": {"name_ar": "هيوسيامين", "class": "antispasmodic", "indications": ["ibs"]},
        "lansoprazole": {"name_ar": "لانسوبرازول", "class": "ppi", "indications": ["gerd"]},
        "magaldrate": {"name_ar": "ماجالدرات", "class": "antacid", "indications": ["gerd"]},
        "mesalamine": {"name_ar": "ميسالامين", "class": "5asa", "indications": ["ibd"]},
        "misoprostol": {"name_ar": "ميزوبروستول", "class": "prostaglandin", "indications": ["ulcer"]},
        "octreotide": {"name_ar": "أوكتريوتيد", "class": "somatostatin", "indications": ["varices"]},
        "polyethylene_glycol": {"name_ar": "بولي إيثيلين جليكول", "class": "laxative", "indications": ["constipation"]},
        "rabeprazole": {"name_ar": "رابيبرازول", "class": "ppi", "indications": ["gerd"]},
        "simethicone": {"name_ar": "سيميثيكون", "class": "antiflatulent", "indications": ["gas"]},
        "sucralfate": {"name_ar": "سوكرالفات", "class": "mucosal_protectant", "indications": ["ulcer"]},
        
        # More diabetes
        "acarbose": {"name_ar": "أكاربوز", "class": "alpha_glucosidase", "indications": ["diabetes_type2"]},
        "canagliflozin": {"name_ar": "كاناجليفلوزين", "class": "sglt2", "indications": ["diabetes_type2"]},
        "exenatide": {"name_ar": "إكسيناتيد", "class": "glp1", "indications": ["diabetes_type2"]},
        "glimepiride": {"name_ar": "جليميبيريد", "class": "sulfonylurea", "indications": ["diabetes_type2"]},
        "glipizide": {"name_ar": "جليبيزيد", "class": "sulfonylurea", "indications": ["diabetes_type2"]},
        "glyburide": {"name_ar": "جليبوريد", "class": "sulfonylurea", "indications": ["diabetes_type2"]},
        "insulin_detemir": {"name_ar": "إنسولين ديتيمير", "class": "insulin", "indications": ["diabetes"]},
        "insulin_lispro": {"name_ar": "إنسولين ليسبرو", "class": "insulin", "indications": ["diabetes"]},
        "insulin_regular": {"name_ar": "إنسولين عادي", "class": "insulin", "indications": ["diabetes"]},
        "nateglinide": {"name_ar": "ناتيجليتنيد", "class": "meglitinide", "indications": ["diabetes_type2"]},
        "repaglinide": {"name_ar": "ريباجلينيد", "class": "meglitinide", "indications": ["diabetes_type2"]},
        "saxagliptin": {"name_ar": "ساكساجليبتين", "class": "dpp4", "indications": ["diabetes_type2"]},
        "vildagliptin": {"name_ar": "فيلداجليبتين", "class": "dpp4", "indications": ["diabetes_type2"]},
        
        # More respiratory
        "aminophylline": {"name_ar": "أمينوفيلين", "class": "xanthine", "indications": ["asthma", "copd"]},
        "cromolyn": {"name_ar": "كرومولين", "class": "mast_cell_stabilizer", "indications": ["asthma"]},
        "fluticasone_salmeterol": {"name_ar": "فلوتيكاسون/سالميتيرول", "class": "ics_laba", "indications": ["asthma", "copd"]},
        "theophylline": {"name_ar": "ثيوفيلين", "class": "xanthine", "indications": ["asthma", "copd"]},
        
        # More pain/inflammation
        "acetaminophen_codeine": {"name_ar": "باراسيتامول/كودايين", "class": "analgesic_combo", "indications": ["pain"]},
        "buprenorphine": {"name_ar": "ببرينورفين", "class": "opioid", "indications": ["pain", "addiction"]},
        "fentanyl": {"name_ar": "فنتانيل", "class": "opioid", "indications": ["severe_pain"]},
        "hydrocodone": {"name_ar": "هيدروكودون", "class": "opioid", "indications": ["pain"]},
        "hydromorphone": {"name_ar": "هيدرومورفون", "class": "opioid", "indications": ["severe_pain"]},
        "indomethacin": {"name_ar": "إندوميثاسين", "class": "nsaid", "indications": ["arthritis", "gout"]},
        "ketorolac": {"name_ar": "كيتورولاك", "class": "nsaid", "indications": ["pain"]},
        "meperidine": {"name_ar": "ميبيريدين", "class": "opioid", "indications": ["pain"]},
        "methadone": {"name_ar": "ميثادون", "class": "opioid", "indications": ["pain", "addiction"]},
        "oxycodone": {"name_ar": "أوكسيكودون", "class": "opioid", "indications": ["pain"]},
        "piroxicam": {"name_ar": "بيروكسيكام", "class": "nsaid", "indications": ["pain", "arthritis"]},
        "sulindac": {"name_ar": "سولينداك", "class": "nsaid", "indications": ["arthritis"]},
        
        # More psych
        "buspirone": {"name_ar": "بوسبيرون", "class": "anxiolytic", "indications": ["anxiety"]},
        "chlordiazepoxide": {"name_ar": "كلورديازيبوكسيد", "class": "benzodiazepine", "indications": ["anxiety"]},
        "chlorpromazine": {"name_ar": "كلوربرومازين", "class": "antipsychotic", "indications": ["schizophrenia"]},
        "clozapine": {"name_ar": "كلوزابين", "class": "antipsychotic", "indications": ["schizophrenia"]},
        "desvenlafaxine": {"name_ar": "ديسفينلافاكسين", "class": "snri", "indications": ["depression"]},
        "fluphenazine": {"name_ar": "فلوثينازين", "class": "antipsychotic", "indications": ["schizophrenia"]},
        "hydroxyzine": {"name_ar": "هيدروكسيزين", "class": "antihistamine", "indications": ["anxiety", "allergy"]},
        "iloperidone": {"name_ar": "إيلوبيريدون", "class": "antipsychotic", "indications": ["schizophrenia"]},
        "lorazepam": {"name_ar": "لورازيبام", "class": "benzodiazepine", "indications": ["anxiety"]},
        "lurasidone": {"name_ar": "لوراسيدون", "class": "antipsychotic", "indications": ["schizophrenia", "bipolar"]},
        "midazolam": {"name_ar": "ميدازولام", "class": "benzodiazepine", "indications": ["sedation"]},
        "oxazepam": {"name_ar": "أوكسازيبام", "class": "benzodiazepine", "indications": ["anxiety"]},
        "paliperidone": {"name_ar": "باليريدون", "class": "antipsychotic", "indications": ["schizophrenia"]},
        "temazepam": {"name_ar": "تيمازيبام", "class": "benzodiazepine", "indications": ["insomnia"]},
        "trazodone": {"name_ar": "ترازودون", "class": "antidepressant", "indications": ["depression", "insomnia"]},
        "triazolam": {"name_ar": "تريازولام", "class": "benzodiazepine", "indications": ["insomnia"]},
        "ziprasidone": {"name_ar": "زيبراسيدون", "class": "antipsychotic", "indications": ["schizophrenia"]},
        
        # More neuro
        "ethosuximide": {"name_ar": "إيثوسوكسيميد", "class": "antiepileptic", "indications": ["epilepsy"]},
        "lacosamide": {"name_ar": "لاكوساميد", "class": "antiepileptic", "indications": ["epilepsy"]},
        "oxcarbazepine": {"name_ar": "أوكسكاربازيبين", "class": "antiepileptic", "indications": ["epilepsy"]},
        "primidone": {"name_ar": "بريميدون", "class": "antiepileptic", "indications": ["epilepsy"]},
        "rufinamide": {"name_ar": "روفيناميد", "class": "antiepileptic", "indications": ["epilepsy"]},
        "tiagabine": {"name_ar": "تياجابين", "class": "antiepileptic", "indications": ["epilepsy"]},
        "vigabatrin": {"name_ar": "فيجاباترين", "class": "antiepileptic", "indications": ["epilepsy"]},
        "zonisamide": {"name_ar": "زونيساميد", "class": "antiepileptic", "indications": ["epilepsy"]},
        
        # Urology more
        "alfuzosin": {"name_ar": "ألفيوزوسين", "class": "alpha_blocker", "indications": ["bph"]},
        "darifenacin": {"name_ar": "داري fenacin", "class": "anticholinergic", "indications": ["overactive_bladder"]},
        "dutasteride": {"name_ar": "دوتاستيريد", "class": "5ari", "indications": ["bph"]},
        "mirabegron": {"name_ar": "ميرابيجون", "class": "beta3_agonist", "indications": ["overactive_bladder"]},
        "solifenacin": {"name_ar": "سوليفيناسين", "class": "anticholinergic", "indications": ["overactive_bladder"]},
        "tolterodine": {"name_ar": "تولتيرودين", "class": "anticholinergic", "indications": ["overactive_bladder"]},
        "vardenafil": {"name_ar": "فاردينافيل", "class": "pde5", "indications": ["ed"]},
        
        # Dermatology more
        "adapalene": {"name_ar": "أدابالين", "class": "retinoid", "indications": ["acne"]},
        "calcipotriene": {"name_ar": "كالسيبوترين", "class": "vitamin_d_analog", "indications": ["psoriasis"]},
        "clobetasol": {"name_ar": "كلوبيتاسول", "class": "corticosteroid", "indications": ["dermatitis"]},
        "imiquimod": {"name_ar": "إيميكيمود", "class": "immune_response_modifier", "indications": ["warts"]},
        "methotrexate_topical": {"name_ar": "ميثوتريكسات موضعي", "class": "dmard", "indications": ["psoriasis"]},
        "permethrin": {"name_ar": "بيرميثرين", "class": "antiparasitic", "indications": ["scabies", "lice"]},
        "podophyllotoxin": {"name_ar": "بودوفيلوتوكسين", "class": "antimitotic", "indications": ["warts"]},
        "salicylic_acid": {"name_ar": "حمض الساليسيليك", "class": "keratolytic", "indications": ["warts", "acne"]},
        "tacrolimus_topical": {"name_ar": "تاكروليموس موضعي", "class": "calcineurin_inhibitor", "indications": ["eczema"]},
        
        # Ophthalmology
        "bimatoprost": {"name_ar": "بيماتوبروست", "class": "prostaglandin", "indications": ["glaucoma"]},
        "brimonidine": {"name_ar": "بريمونيدين", "class": "alpha_agonist", "indications": ["glaucoma"]},
        "dorzolamide": {"name_ar": "دورزولاميد", "class": "carbonic_anhydrase", "indications": ["glaucoma"]},
        "olopatadine": {"name_ar": "أولوباتادين", "class": "antihistamine", "indications": ["allergic_conjunctivitis"]},
        "travoprost": {"name_ar": "ترافوبروست", "class": "prostaglandin", "indications": ["glaucoma"]},
        
        # ENT
        "fluticasone_nasal": {"name_ar": "فلوتيكاسون أنفي", "class": "corticosteroid", "indications": ["rhinitis"]},
        "mometasone_nasal": {"name_ar": "موميتازون أنفي", "class": "corticosteroid", "indications": ["rhinitis"]},
        "oxymetazoline": {"name_ar": "أوكسي ميتازولين", "class": "decongestant", "indications": ["congestion"]},
        "xylometazoline": {"name_ar": "زايلو ميتازولين", "class": "decongestant", "indications": ["congestion"]},
        
        # Rheumatology
        "abatacept": {"name_ar": "أباتاسيبت", "class": "biologic", "indications": ["ra"]},
        "anakinra": {"name_ar": "أناكينرا", "class": "biologic", "indications": ["ra"]},
        "certolizumab": {"name_ar": "سيرتوليزوماب", "class": "biologic", "indications": ["ra", "crohn"]},
        "golimumab": {"name_ar": "جوليموماب", "class": "biologic", "indications": ["ra"]},
        "leflunomide": {"name_ar": "ليفلونوميد", "class": "dmard", "indications": ["ra"]},
        "sulfasalazine": {"name_ar": "سلفاسالازين", "class": "dmard", "indications": ["ra", "ibd"]},
        "tofacitinib": {"name_ar": "توفاسيتينيب", "class": "jak_inhibitor", "indications": ["ra"]},
        "ustekinumab": {"name_ar": "أوستيكينوماب", "class": "biologic", "indications": ["psoriasis", "crohn"]},
        
        # Oncology
        "capecitabine": {"name_ar": "كابيسيتابين", "class": "antimetabolite", "indications": ["cancer"]},
        "carboplatin": {"name_ar": "كاربوبلاتين", "class": "alkylating", "indications": ["cancer"]},
        "cisplatin": {"name_ar": "سيسبلاتين", "class": "alkylating", "indications": ["cancer"]},
        "cyclophosphamide": {"name_ar": "سيكلوفوسفاميد", "class": "alkylating", "indications": ["cancer", "autoimmune"]},
        "docetaxel": {"name_ar": "دوسيتاكسيل", "class": "taxane", "indications": ["cancer"]},
        "doxorubicin": {"name_ar": "دوكسوروبيسين", "class": "anthracycline", "indications": ["cancer"]},
        "etoposide": {"name_ar": "إيتوبوسيد", "class": "topoisomerase", "indications": ["cancer"]},
        "fluorouracil": {"name_ar": "فلورويوراسيل", "class": "antimetabolite", "indications": ["cancer"]},
        "gemcitabine": {"name_ar": "جيمسيتابين", "class": "antimetabolite", "indications": ["cancer"]},
        "imatinib": {"name_ar": "إيماتينيب", "class": "tki", "indications": ["cml"]},
        "irinotecan": {"name_ar": "إيرينوتيكان", "class": "topoisomerase", "indications": ["cancer"]},
        "methotrexate_oncology": {"name_ar": "ميثوتريكسات (أورام)", "class": "antimetabolite", "indications": ["cancer"]},
        "paclitaxel": {"name_ar": "باكليتاكسيل", "class": "taxane", "indications": ["cancer"]},
        "rituximab_oncology": {"name_ar": "ريتوكسيماب (أورام)", "class": "biologic", "indications": ["lymphoma"]},
        "tamoxifen": {"name_ar": "تاموكسيفين", "class": "serm", "indications": ["breast_cancer"]},
        "trastuzumab_oncology": {"name_ar": "تراستوزوماب (أورام)", "class": "biologic", "indications": ["breast_cancer"]},
        "vinblastine": {"name_ar": "فينبلاستين", "class": "vinca", "indications": ["cancer"]},
        "vincristine": {"name_ar": "فينكريستين", "class": "vinca", "indications": ["cancer"]},
        
        # More supplements
        "biotin": {"name_ar": "بيوتين", "class": "vitamin", "indications": ["deficiency"]},
        "calcium_citrate": {"name_ar": "سترات الكالسيوم", "class": "mineral", "indications": ["deficiency"]},
        "coenzyme_q10": {"name_ar": "إنزيم Q10", "class": "supplement", "indications": ["cardiovascular"]},
        "copper": {"name_ar": "نحاس", "class": "mineral", "indications": ["deficiency"]},
        "iodine": {"name_ar": "يود", "class": "mineral", "indications": ["thyroid"]},
        "multivitamin": {"name_ar": "مالتي فيتامين", "class": "vitamin", "indications": ["deficiency"]},
        "potassium_chloride": {"name_ar": "كلوريد البوتاسيوم", "class": "mineral", "indications": ["deficiency"]},
        "selenium": {"name_ar": "سيلينيوم", "class": "mineral", "indications": ["deficiency"]},
        "vitamin_a": {"name_ar": "فيتامين أ", "class": "vitamin", "indications": ["deficiency"]},
        "vitamin_b1": {"name_ar": "فيتامين ب١", "class": "vitamin", "indications": ["deficiency"]},
        "vitamin_b6": {"name_ar": "فيتامين ب٦", "class": "vitamin", "indications": ["deficiency"]},
        "vitamin_c": {"name_ar": "فيتامين ج", "class": "vitamin", "indications": ["deficiency"]},
        "vitamin_e": {"name_ar": "فيتامين هـ", "class": "vitamin", "indications": ["deficiency"]},
        "vitamin_k": {"name_ar": "فيتامين ك", "class": "vitamin", "indications": ["deficiency"]},
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
    data["version"] = "5.0"
    data["updated_at"] = datetime.now().isoformat()
    save_json(path, data)
    
    print(f"   Before: {before}")
    print(f"   Added: {added}")
    print(f"   After: {len(drugs)}")


# ═══════════════════════════════════════════════════════
# 2. EXTENDED INTERACTIONS (target: 300+)
# ═══════════════════════════════════════════════════════
def extend_interactions():
    print("\n⚠️  Extending interactions...")
    path = DATA / "interactions.json"
    data = load_json(path)
    interactions = data.get("interactions", [])
    before = len(interactions)
    
    NEW_INTERACTIONS = [
        # More interactions
        {"drug1": "warfarin", "drug2": "amiodarone", "severity": "major", "effect": "زيادة تأثير الوارفارين", "action": "تقليل الجرعة"},
        {"drug1": "warfarin", "drug2": "rifampin", "severity": "major", "effect": "انخفاض تأثير الوارفارين", "action": "زيادة الجرعة"},
        {"drug1": "warfarin", "drug2": "carbamazepine", "severity": "major", "effect": "انخفاض تأثير الوارفارين", "action": "مراقبة INR"},
        {"drug1": "warfarin", "drug2": "phenytoin", "severity": "major", "effect": "زيادة ثم انخفاض", "action": "مراقبة لصيقة"},
        {"drug1": "warfarin", "drug2": "levothyroxine", "severity": "moderate", "effect": "زيادة تأثير الوارفارين", "action": "مراقبة INR"},
        
        {"drug1": "clopidogrel", "drug2": "omeprazole", "severity": "major", "effect": "انخفاض تأثير الكلوبيدوجريل", "action": "استخدم pantoprazole"},
        {"drug1": "clopidogrel", "drug2": "esomeprazole", "severity": "major", "effect": "انخفاض التأثير", "action": "تجنب"},
        
        {"drug1": "metformin", "drug2": "alcohol", "severity": "major", "effect": "خطر الحماض اللبني", "action": "تجنب الكحول"},
        {"drug1": "metformin", "drug2": "furosemide", "severity": "moderate", "effect": "زيادة خطر الحماض", "action": "مراقبة"},
        {"drug1": "glimepiride", "drug2": "alcohol", "severity": "moderate", "effect": "خطر نقص السكر", "action": "تجنب"},
        
        {"drug1": "simvastatin", "drug2": "gemfibrozil", "severity": "major", "effect": "خطر التهاب عضلي", "action": "تجنب"},
        {"drug1": "simvastatin", "drug2": "cyclosporine", "severity": "major", "effect": "خطر التهاب عضلي", "action": "تجنب"},
        {"drug1": "simvastatin", "drug2": "verapamil", "severity": "moderate", "effect": "زيادة تركيز الستاتين", "action": "تقليل الجرعة"},
        {"drug1": "simvastatin", "drug2": "diltiazem", "severity": "moderate", "effect": "زيادة تركيز الستاتين", "action": "تقليل الجرعة"},
        {"drug1": "atorvastatin", "drug2": "itraconazole", "severity": "major", "effect": "خطر التهاب عضلي", "action": "تجنب"},
        
        {"drug1": "ssri", "drug2": "maoi", "severity": "contraindicated", "effect": "متلازمة السيروتونين", "action": "ممنوع تماماً"},
        {"drug1": "ssri", "drug2": "linezolid", "severity": "major", "effect": "متلازمة السيروتونين", "action": "تجنب"},
        {"drug1": "ssri", "drug2": "triptan", "severity": "moderate", "effect": "متلازمة السيروتونين", "action": "مراقبة"},
        
        {"drug1": "digoxin", "drug2": "verapamil", "severity": "major", "effect": "زيادة تركيز الديجوكسين", "action": "تقليل الجرعة"},
        {"drug1": "digoxin", "drug2": "quinidine", "severity": "major", "effect": "زيادة سمية الديجوكسين", "action": "تقليل الجرعة 50%"},
        {"drug1": "digoxin", "drug2": "amiodarone", "severity": "major", "effect": "زيادة تركيز الديجوكسين", "action": "تقليل الجرعة 50%"},
        {"drug1": "digoxin", "drug2": "clarithromycin", "severity": "major", "effect": "زيادة تركيز الديجوكسين", "action": "مراقبة"},
        
        {"drug1": "ace_inhibitor", "drug2": "spironolactone", "severity": "major", "effect": "ارتفاع البوتاسيوم", "action": "مراقبة البوتاسيوم"},
        {"drug1": "ace_inhibitor", "drug2": "nsaid", "severity": "moderate", "effect": "انخفاض تأثير الضغط + كلى", "action": "مراقبة"},
        {"drug1": "ace_inhibitor", "drug2": "potassium_chloride", "severity": "major", "effect": "ارتفاع البوتاسيوم", "action": "مراقبة"},
        {"drug1": "ace_inhibitor", "drug2": "lithium", "severity": "major", "effect": "زيادة سمية الليثيوم", "action": "مراقبة"},
        
        {"drug1": "amlodipine", "drug2": "simvastatin", "severity": "moderate", "effect": "زيادة تركيز الستاتين", "action": "تقليل الجرعة"},
        {"drug1": "nifedipine", "drug2": "grapefruit", "severity": "moderate", "effect": "زيادة تركيز النيفيديبين", "action": "تجنب الجريب فروت"},
        {"drug1": "verapamil", "drug2": "beta_blocker", "severity": "major", "effect": "بطء القلب الشديد", "action": "تجنب"},
        
        {"drug1": "beta_blocker", "drug2": "verapamil", "severity": "major", "effect": "بطء القلب", "action": "تجنب"},
        {"drug1": "beta_blocker", "drug2": "insulin", "severity": "moderate", "effect": "إخفاء أعراض نقص السكر", "action": "مراقبة"},
        {"drug1": "beta_blocker", "drug2": "albuterol", "severity": "moderate", "effect": "تضاد التأثير", "action": "استخدم β1-selective"},
        
        {"drug1": "nitrate", "drug2": "pde5", "severity": "contraindicated", "effect": "انخفاض ضغط شديد", "action": "ممنوع تماماً"},
        {"drug1": "nitrate", "drug2": "sildenafil", "severity": "contraindicated", "effect": "انخفاض ضغط خطير", "action": "ممنوع"},
        
        {"drug1": "lithium", "drug2": "nsaid", "severity": "major", "effect": "زيادة سمية الليثيوم", "action": "تجنب"},
        {"drug1": "lithium", "drug2": "thiazide", "severity": "major", "effect": "زيادة سمية الليثيوم", "action": "تقليل الجرعة"},
        {"drug1": "lithium", "drug2": "ace_inhibitor", "severity": "major", "effect": "زيادة سمية الليثيوم", "action": "مراقبة"},
        
        {"drug1": "methotrexate", "drug2": "nsaid", "severity": "major", "effect": "زيادة سمية الميثوتريكسات", "action": "تجنب"},
        {"drug1": "methotrexate", "drug2": "trimethoprim", "severity": "major", "effect": "سمية نقية للدم", "action": "تجنب"},
        {"drug1": "methotrexate", "drug2": "penicillin", "severity": "moderate", "effect": "زيادة تركيز MTX", "action": "مراقبة"},
        
        {"drug1": "allopurinol", "drug2": "azathioprine", "severity": "major", "effect": "سمية نقية للدم", "action": "تقليل الجرعة 75%"},
        {"drug1": "allopurinol", "drug2": "mercaptopurine", "severity": "major", "effect": "سمية نقية للدم", "action": "تقليل الجرعة 75%"},
        {"drug1": "allopurinol", "drug2": "amoxicillin", "severity": "moderate", "effect": "زيادة خطر الطفح الجلدي", "action": "مراقبة"},
        
        {"drug1": "colchicine", "drug2": "clarithromycin", "severity": "major", "effect": "سمية الكولشيسين", "action": "تجنب"},
        {"drug1": "colchicine", "drug2": "cyclosporine", "severity": "major", "effect": "سمية الكولشيسين", "action": "تجنب"},
        {"drug1": "colchicine", "drug2": "verapamil", "severity": "major", "effect": "زيادة السمية", "action": "تقليل الجرعة"},
        
        {"drug1": "metronidazole", "drug2": "alcohol", "severity": "major", "effect": "تفاعل ديسولفيرام", "action": "تجنب الكحول"},
        {"drug1": "metronidazole", "drug2": "warfarin", "severity": "major", "effect": "زيادة تأثير الوارفارين", "action": "تقليل الجرعة"},
        
        {"drug1": "phenytoin", "drug2": "warfarin", "severity": "major", "effect": "تغيرات متقلبة في INR", "action": "مراقبة لصيقة"},
        {"drug1": "phenytoin", "drug2": "carbamazepine", "severity": "moderate", "effect": "تفاعل معقد", "action": "مراقبة المستويات"},
        {"drug1": "phenytoin", "drug2": "omeprazole", "severity": "moderate", "effect": "زيادة تركيز الفينيتوين", "action": "مراقبة"},
        
        {"drug1": "levothyroxine", "drug2": "calcium_carbonate", "severity": "moderate", "effect": "انخفاض الامتصاص", "action": "افصل 4 ساعات"},
        {"drug1": "levothyroxine", "drug2": "iron_sulfate", "severity": "moderate", "effect": "انخفاض الامتصاص", "action": "افصل 4 ساعات"},
        {"drug1": "levothyroxine", "drug2": "omeprazole", "severity": "moderate", "effect": "انخفاض الامتصاص", "action": "مراقبة TSH"},
        {"drug1": "levothyroxine", "drug2": "warfarin", "severity": "moderate", "effect": "زيادة تأثير الوارفارين", "action": "مراقبة"},
        
        {"drug1": "ciprofloxacin", "drug2": "antacid", "severity": "moderate", "effect": "انخفاض الامتصاص", "action": "افصل بينهم"},
        {"drug1": "ciprofloxacin", "drug2": "theophylline", "severity": "major", "effect": "زيادة تركيز الثيوفيلين", "action": "تقليل الجرعة"},
        {"drug1": "ciprofloxacin", "drug2": "warfarin", "severity": "major", "effect": "زيادة تأثير الوارفارين", "action": "مراقبة INR"},
        {"drug1": "ciprofloxacin", "drug2": "tizanidine", "severity": "contraindicated", "effect": "انخفاض ضغط + تخدير", "action": "ممنوع"},
        
        {"drug1": "clarithromycin", "drug2": "simvastatin", "severity": "major", "effect": "خطر التهاب عضلي", "action": "إيقاف الستاتين"},
        {"drug1": "clarithromycin", "drug2": "warfarin", "severity": "major", "effect": "زيادة تأثير الوارفارين", "action": "مراقبة INR"},
        {"drug1": "clarithromycin", "drug2": "digoxin", "severity": "major", "effect": "زيادة سمية الديجوكسين", "action": "مراقبة"},
        
        {"drug1": "tramadol", "drug2": "ssri", "severity": "major", "effect": "متلازمة السيروتونين", "action": "تجنب"},
        {"drug1": "tramadol", "drug2": "maoi", "severity": "contraindicated", "effect": "متلازمة السيروتونين", "action": "ممنوع"},
        {"drug1": "tramadol", "drug2": "carbamazepine", "severity": "moderate", "effect": "انخفاض تأثير الترامادول", "action": "مراقبة"},
        
        {"drug1": "benzodiazepine", "drug2": "opioid", "severity": "major", "effect": "تثبيط الجهاز التنفسي", "action": "تجنب"},
        {"drug1": "benzodiazepine", "drug2": "alcohol", "severity": "major", "effect": "تثبيط CNS", "action": "تجنب"},
        {"drug1": "benzodiazepine", "drug2": "clozapine", "severity": "moderate", "effect": "تثبيط CNS", "action": "مراقبة"},
        
        {"drug1": "metoclopramide", "drug2": "antipsychotic", "severity": "major", "effect": "أعراض خارج هرمية", "action": "تجنب"},
        {"drug1": "metoclopramide", "drug2": "ssri", "severity": "moderate", "effect": "متلازمة السيروتونين", "action": "مراقبة"},
        
        {"drug1": "ondansetron", "drug2": "apomorphine", "severity": "contraindicated", "effect": "انخفاض ضغط شديد", "action": "ممنوع"},
        {"drug1": "ondansetron", "drug2": "ssri", "severity": "moderate", "effect": "QT prolongation", "action": "مراقبة ECG"},
        
        {"drug1": "amiodarone", "drug2": "warfarin", "severity": "major", "effect": "زيادة تأثير الوارفارين", "action": "تقليل الجرعة 50%"},
        {"drug1": "amiodarone", "drug2": "digoxin", "severity": "major", "effect": "زيادة سمية الديجوكسين", "action": "تقليل الجرعة 50%"},
        {"drug1": "amiodarone", "drug2": "beta_blocker", "severity": "major", "effect": "بطء القلب", "action": "مراقبة"},
        
        {"drug1": "spironolactone", "drug2": "potassium_chloride", "severity": "major", "effect": "ارتفاع البوتاسيوم", "action": "تجنب"},
        {"drug1": "spironolactone", "drug2": "nsaid", "severity": "moderate", "effect": "انخفاض تأثير المدر", "action": "مراقبة"},
        
        {"drug1": "furosemide", "drug2": "nsaid", "severity": "moderate", "effect": "انخفاض تأثير المدر", "action": "مراقبة"},
        {"drug1": "furosemide", "drug2": "aminoglycoside", "severity": "major", "effect": "زيادة سمية الأذن", "action": "تجنب"},
        {"drug1": "furosemide", "drug2": "digoxin", "severity": "moderate", "effect": "نقص البوتاسيوم", "action": "تعويض البوتاسيوم"},
        
        {"drug1": "octreotide", "drug2": "insulin", "severity": "moderate", "effect": "تغيير مستويات السكر", "action": "مراقبة"},
        
        {"drug1": "sildenafil", "drug2": "nitrate", "severity": "contraindicated", "effect": "انخفاض ضغط شديد", "action": "ممنوع"},
        {"drug1": "sildenafil", "drug2": "alpha_blocker", "severity": "moderate", "effect": "انخفاض ضغط", "action": "مراقبة"},
        
        {"drug1": "levodopa", "drug2": "antipsychotic", "severity": "major", "effect": "تضاد التأثير", "action": "تجنب"},
        {"drug1": "levodopa", "drug2": "metoclopramide", "severity": "major", "effect": "تضاد التأثير", "action": "تجنب"},
        {"drug1": "levodopa", "drug2": "maoi", "severity": "major", "effect": "ارتفاع ضغط شديد", "action": "تجنب"},
        
        {"drug1": "carbamazepine", "drug2": "oral_contraceptive", "severity": "major", "effect": "انخفاض فعالية الحمل", "action": "استخدم طريقة أخرى"},
        {"drug1": "carbamazepine", "drug2": "warfarin", "severity": "major", "effect": "انخفاض تأثير الوارفارين", "action": "مراقبة"},
        {"drug1": "carbamazepine", "drug2": "valproic_acid", "severity": "moderate", "effect": "انخفاض مستويات الاثنين", "action": "مراقبة"},
        
        {"drug1": "phenytoin", "drug2": "oral_contraceptive", "severity": "major", "effect": "انخفاض فعالية الحمل", "action": "استخدم طريقة أخرى"},
        {"drug1": "rifampin", "drug2": "oral_contraceptive", "severity": "major", "effect": "انخفاض فعالية الحمل", "action": "استخدم طريقة أخرى"},
        
        {"drug1": "tamoxifen", "drug2": "ssri", "severity": "major", "effect": "انخفاض فعالية تاموكسيفين", "action": "استخدم venlafaxine"},
        {"drug1": "tamoxifen", "drug2": "warfarin", "severity": "major", "effect": "زيادة خطر النزيف", "action": "مراقبة"},
        
        {"drug1": "methotrexate", "drug2": "ibuprofen", "severity": "major", "effect": "زيادة سمية MTX", "action": "تجنب"},
        {"drug1": "methotrexate", "drug2": "aspirin", "severity": "major", "effect": "زيادة سمية MTX", "action": "تجنب"},
        {"drug1": "methotrexate", "drug2": "penicillin", "severity": "moderate", "effect": "زيادة تركيز MTX", "action": "مراقبة"},
        
        {"drug1": "statins", "drug2": "grapefruit", "severity": "moderate", "effect": "زيادة تركيز الستاتين", "action": "تجنب الجريب فروت"},
        {"drug1": "amlodipine", "drug2": "grapefruit", "severity": "moderate", "effect": "زيادة تركيز الأملوديبين", "action": "تجنب"},
        
        {"drug1": "potassium", "drug2": "ace_inhibitor", "severity": "major", "effect": "ارتفاع البوتاسيوم", "action": "تجنب"},
        {"drug1": "potassium", "drug2": "spironolactone", "severity": "major", "effect": "ارتفاع البوتاسيوم", "action": "تجنب"},
    ]
    
    # Dedupe existing
    existing_pairs = set()
    for i in interactions:
        d1 = i.get("drug1", "").lower()
        d2 = i.get("drug2", "").lower()
        existing_pairs.add((d1, d2))
        existing_pairs.add((d2, d1))
    
    added = 0
    for new_int in NEW_INTERACTIONS:
        d1 = new_int["drug1"].lower()
        d2 = new_int["drug2"].lower()
        pair = (d1, d2)
        if pair not in existing_pairs:
            interactions.append(new_int)
            existing_pairs.add(pair)
            existing_pairs.add((d2, d1))
            added += 1
    
    data["interactions"] = interactions
    data["version"] = "4.0"
    data["updated_at"] = datetime.now().isoformat()
    save_json(path, data)
    
    print(f"   Before: {before}")
    print(f"   Added: {added}")
    print(f"   After: {len(interactions)}")


# ═══════════════════════════════════════════════════════
# 3. EXTENDED SYMPTOMS (target: 100+)
# ═══════════════════════════════════════════════════════
def extend_symptoms():
    print("\n🩺 Extending symptoms...")
    path = DATA / "symptoms.json"
    data = load_json(path)
    symptoms = data.get("symptoms", {})
    before = len(symptoms)
    
    NEW_SYMPTOMS = {
        "headache": {"name_ar": "صداع", "related_conditions": ["tension_headache", "migraine", "hypertension"]},
        "fever": {"name_ar": "حمى", "related_conditions": ["infection", "flu", "covid"]},
        "cough": {"name_ar": "كحة", "related_conditions": ["cold", "flu", "bronchitis"]},
        "sore_throat": {"name_ar": "التهاب الحلق", "related_conditions": ["cold", "flu", "strep"]},
        "runny_nose": {"name_ar": "رشح", "related_conditions": ["cold", "allergy"]},
        "nausea": {"name_ar": "غثيان", "related_conditions": ["gastroenteritis", "migraine", "pregnancy"]},
        "vomiting": {"name_ar": "قيء", "related_conditions": ["gastroenteritis", "food_poisoning"]},
        "diarrhea": {"name_ar": "إسهال", "related_conditions": ["gastroenteritis", "ibs", "food_poisoning"]},
        "constipation": {"name_ar": "إمساك", "related_conditions": ["ibs", "dehydration"]},
        "abdominal_pain": {"name_ar": "ألم في البطن", "related_conditions": ["gastritis", "ibs", "appendicitis"]},
        "heartburn": {"name_ar": "حرقة المعدة", "related_conditions": ["gerd", "gastritis"]},
        "bloating": {"name_ar": "انتفاخ", "related_conditions": ["ibs", "gas"]},
        "fatigue": {"name_ar": "إرهاق", "related_conditions": ["anemia", "thyroid", "diabetes"]},
        "dizziness": {"name_ar": "دوخة", "related_conditions": ["vertigo", "anemia", "hypotension"]},
        "chest_pain": {"name_ar": "ألم في الصدر", "related_conditions": ["heart_attack", "angina", "gerd"], "emergency": True},
        "shortness_of_breath": {"name_ar": "ضيق في التنفس", "related_conditions": ["asthma", "heart_failure", "anxiety"], "emergency": True},
        "palpitations": {"name_ar": "خفقان", "related_conditions": ["arrhythmia", "anxiety", "hyperthyroidism"]},
        "rash": {"name_ar": "طفح جلدي", "related_conditions": ["allergy", "eczema", "infection"]},
        "itching": {"name_ar": "حكة", "related_conditions": ["allergy", "eczema", "fungal"]},
        "swelling": {"name_ar": "تورم", "related_conditions": ["edema", "allergy", "injury"]},
        "joint_pain": {"name_ar": "ألم في المفاصل", "related_conditions": ["arthritis", "gout", "injury"]},
        "muscle_pain": {"name_ar": "ألم في العضلات", "related_conditions": ["flu", "overuse", "statin_side_effect"]},
        "back_pain": {"name_ar": "ألم في الظهر", "related_conditions": ["muscle_strain", "disc_herniation", "kidney"]},
        "neck_pain": {"name_ar": "ألم في الرقبة", "related_conditions": ["muscle_strain", "cervical"]},
        "insomnia": {"name_ar": "أرق", "related_conditions": ["anxiety", "depression", "sleep_apnea"]},
        "anxiety": {"name_ar": "قلق", "related_conditions": ["gad", "panic"]},
        "depression": {"name_ar": "اكتئاب", "related_conditions": ["mdd", "bipolar"]},
        "memory_loss": {"name_ar": "فقدان الذاكرة", "related_conditions": ["dementia", "alzheimer"]},
        "confusion": {"name_ar": "ارتباك", "related_conditions": ["delirium", "infection"]},
        "seizure": {"name_ar": "تشنجات", "related_conditions": ["epilepsy", "fever"], "emergency": True},
        "vision_blur": {"name_ar": "عدم وضوح الرؤية", "related_conditions": ["diabetes", "hypertension", "eye"]},
        "eye_pain": {"name_ar": "ألم في العين", "related_conditions": ["glaucoma", "infection"]},
        "ear_pain": {"name_ar": "ألم في الأذن", "related_conditions": ["otitis", "infection"]},
        "hearing_loss": {"name_ar": "فقدان السمع", "related_conditions": ["otitis", "wax", "presbycusis"]},
        "tooth_pain": {"name_ar": "ألم الأسنان", "related_conditions": ["caries", "abscess"]},
        "urinary_pain": {"name_ar": "ألم عند التبول", "related_conditions": ["uti", "cystitis"]},
        "frequent_urination": {"name_ar": "كثرة التبول", "related_conditions": ["diabetes", "uti", "bph"]},
        "blood_in_urine": {"name_ar": "دم في البول", "related_conditions": ["uti", "kidney_stone"], "emergency": True},
        "weight_loss": {"name_ar": "فقدان الوزن", "related_conditions": ["diabetes", "thyroid", "cancer"]},
        "weight_gain": {"name_ar": "زيادة الوزن", "related_conditions": ["hypothyroidism", "diabetes"]},
        "excessive_thirst": {"name_ar": "عطش شديد", "related_conditions": ["diabetes", "dehydration"]},
        "excessive_hunger": {"name_ar": "جوع شديد", "related_conditions": ["diabetes", "hyperthyroidism"]},
        "night_sweats": {"name_ar": "تعرق ليلي", "related_conditions": ["tb", "menopause", "lymphoma"]},
        "hair_loss": {"name_ar": "تساقط الشعر", "related_conditions": ["thyroid", "alopecia", "deficiency"]},
        "skin_discoloration": {"name_ar": "تغير لون الجلد", "related_conditions": ["jaundice", "bruise"]},
        "numbness": {"name_ar": "تنميل", "related_conditions": ["neuropathy", "stroke", "b12_deficiency"]},
        "tingling": {"name_ar": "وخز", "related_conditions": ["neuropathy", "b12_deficiency"]},
        "tremor": {"name_ar": "رجفة", "related_conditions": ["parkinson", "hyperthyroidism"]},
        "difficulty_swallowing": {"name_ar": "صعوبة البلع", "related_conditions": ["esophagitis", "stroke"]},
        "hoarseness": {"name_ar": "بحة في الصوت", "related_conditions": ["laryngitis", "thyroid"]},
        "cold_intolerance": {"name_ar": "عدم تحمل البرد", "related_conditions": ["hypothyroidism"]},
        "heat_intolerance": {"name_ar": "عدم تحمل الحر", "related_conditions": ["hyperthyroidism"]},
        "breast_lump": {"name_ar": "كتلة في الثدي", "related_conditions": ["breast_cancer", "fibroadenoma"]},
        "vaginal_discharge": {"name_ar": "إفرازات مهبلية", "related_conditions": ["infection", "candida"]},
        "menstrual_irregularity": {"name_ar": "عدم انتظام الدورة", "related_conditions": ["pcos", "thyroid"]},
        "impotence": {"name_ar": "ضعف جنسي", "related_conditions": ["ed", "diabetes"]},
        "loss_of_appetite": {"name_ar": "فقدان الشهية", "related_conditions": ["depression", "cancer"]},
        "increased_appetite": {"name_ar": "زيادة الشهية", "related_conditions": ["diabetes", "hyperthyroidism"]},
        "dark_urine": {"name_ar": "بول داكن", "related_conditions": ["dehydration", "liver"]},
        "yellow_skin": {"name_ar": "اصفرار الجلد", "related_conditions": ["jaundice", "liver"]},
        "pale_skin": {"name_ar": "شحوب", "related_conditions": ["anemia", "shock"]},
        "bruising": {"name_ar": "كدمات", "related_conditions": ["bleeding_disorder", "liver"]},
        "bleeding_gums": {"name_ar": "نزيف اللثة", "related_conditions": ["gum_disease", "bleeding_disorder"]},
        "nosebleed": {"name_ar": "نزيف الأنف", "related_conditions": ["hypertension", "bleeding_disorder"]},
        "back_stiffness": {"name_ar": "تصلب الظهر", "related_conditions": ["arthritis", "injury"]},
        "leg_swelling": {"name_ar": "تورم الساق", "related_conditions": ["dvt", "heart_failure", "edema"]},
        "cold_sweat": {"name_ar": "تعرق بارد", "related_conditions": ["heart_attack", "shock"], "emergency": True},
    }
    
    added = 0
    for key, info in NEW_SYMPTOMS.items():
        if key not in symptoms:
            symptoms[key] = info
            added += 1
    
    data["symptoms"] = symptoms
    data["version"] = "3.0"
    data["updated_at"] = datetime.now().isoformat()
    save_json(path, data)
    
    print(f"   Before: {before}")
    print(f"   Added: {added}")
    print(f"   After: {len(symptoms)}")


if __name__ == "__main__":
    print("═══════════════════════════════════════════════════")
    print("  Extended Data Expansion")
    print("═══════════════════════════════════════════════════")
    
    extend_drugs()
    extend_interactions()
    extend_symptoms()
    
    print("\n═══════════════════════════════════════════════════")
    print("  ✅ Extended expansion complete")
    print("═══════════════════════════════════════════════════")
