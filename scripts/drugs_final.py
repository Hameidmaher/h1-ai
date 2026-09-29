#!/usr/bin/env python3
"""Add remaining drugs"""
import json
from pathlib import Path

DRUGS_PATH = Path.home() / "h1-ai" / "data" / "drugs.json"
data = json.load(open(DRUGS_PATH, encoding="utf-8"))
drugs = data.get("drugs", {})
print(f"\n📊 Current drugs: {len(drugs)}\n")

NEW = {
    "timolol": {"name_ar": "تيمولول", "name_en": "Timolol", "aliases": ["timoptic"], "class": "beta_blocker_eye", "indications": ["glaucoma"], "safe_pregnancy": False, "safe_children": True},
    "latanoprost": {"name_ar": "لاتانوبروست", "name_en": "Latanoprost", "aliases": ["xalatan"], "class": "prostaglandin", "indications": ["glaucoma"], "safe_pregnancy": False, "safe_children": True},
    "levothyroxine": {"name_ar": "ليفوثيروكسين", "name_en": "Levothyroxine", "aliases": ["synthroid"], "class": "thyroid_hormone", "indications": ["hypothyroidism"], "safe_pregnancy": True, "safe_children": True},
    "allopurinol": {"name_ar": "ألوبيورينول", "name_en": "Allopurinol", "aliases": ["zyloprim"], "class": "xanthine_oxidase", "indications": ["gout"], "safe_pregnancy": True, "safe_children": True},
    "colchicine": {"name_ar": "كولشيسين", "name_en": "Colchicine", "aliases": [], "class": "anti_gout", "indications": ["gout"], "safe_pregnancy": False, "safe_children": False},
    "prednisone": {"name_ar": "بريدنيزون", "name_en": "Prednisone", "aliases": [], "class": "corticosteroid", "indications": ["inflammation"], "safe_pregnancy": False, "safe_children": True},
    "prednisolone": {"name_ar": "بريدنيزولون", "name_en": "Prednisolone", "aliases": [], "class": "corticosteroid", "indications": ["inflammation"], "safe_pregnancy": False, "safe_children": True},
    "dexamethasone": {"name_ar": "ديكساميثازون", "name_en": "Dexamethasone", "aliases": [], "class": "corticosteroid", "indications": ["inflammation"], "safe_pregnancy": True, "safe_children": True},
    "methotrexate": {"name_ar": "ميثوتريكسات", "name_en": "Methotrexate", "aliases": [], "class": "dmard", "indications": ["ra", "cancer"], "safe_pregnancy": False, "safe_children": False},
    "hydroxychloroquine": {"name_ar": "هيدروكسيكلوروكين", "name_en": "Hydroxychloroquine", "aliases": ["plaquenil"], "class": "dmard", "indications": ["ra", "lupus"], "safe_pregnancy": True, "safe_children": True},
    "sertraline": {"name_ar": "سيرترالين", "name_en": "Sertraline", "aliases": ["zoloft"], "class": "ssri", "indications": ["depression"], "safe_pregnancy": False, "safe_children": False},
    "fluoxetine": {"name_ar": "فلوكستين", "name_en": "Fluoxetine", "aliases": ["prozac"], "class": "ssri", "indications": ["depression", "ocd"], "safe_pregnancy": False, "safe_children": True},
    "paroxetine": {"name_ar": "باروكستين", "name_en": "Paroxetine", "aliases": ["paxil"], "class": "ssri", "indications": ["depression"], "safe_pregnancy": False, "safe_children": False},
    "escitalopram": {"name_ar": "إسيتالوبرام", "name_en": "Escitalopram", "aliases": ["lexapro"], "class": "ssri", "indications": ["depression"], "safe_pregnancy": False, "safe_children": False},
    "venlafaxine": {"name_ar": "فينلافاكسين", "name_en": "Venlafaxine", "aliases": ["effexor"], "class": "snri", "indications": ["depression"], "safe_pregnancy": False, "safe_children": False},
    "duloxetine": {"name_ar": "دولوكستين", "name_en": "Duloxetine", "aliases": ["cymbalta"], "class": "snri", "indications": ["depression", "neuropathy"], "safe_pregnancy": False, "safe_children": False},
    "bupropion": {"name_ar": "بوبروبيون", "name_en": "Bupropion", "aliases": ["wellbutrin"], "class": "ndri", "indications": ["depression", "smoking_cessation"], "safe_pregnancy": False, "safe_children": False},
    "mirtazapine": {"name_ar": "ميرتازابين", "name_en": "Mirtazapine", "aliases": ["remeron"], "class": "tetracyclic", "indications": ["depression"], "safe_pregnancy": False, "safe_children": False},
    "clonazepam": {"name_ar": "كلونازيبام", "name_en": "Clonazepam", "aliases": ["rivotril"], "class": "benzodiazepine", "indications": ["epilepsy", "anxiety"], "safe_pregnancy": False, "safe_children": True},
    "diazepam": {"name_ar": "ديازيبام", "name_en": "Diazepam", "aliases": ["valium"], "class": "benzodiazepine", "indications": ["anxiety"], "safe_pregnancy": False, "safe_children": True},
    "alprazolam": {"name_ar": "ألبرازولام", "name_en": "Alprazolam", "aliases": ["xanax"], "class": "benzodiazepine", "indications": ["anxiety"], "safe_pregnancy": False, "safe_children": False},
    "zolpidem": {"name_ar": "زولبيديم", "name_en": "Zolpidem", "aliases": ["ambien"], "class": "hypnotic", "indications": ["insomnia"], "safe_pregnancy": False, "safe_children": False},
    "quetiapine": {"name_ar": "كويتيابين", "name_en": "Quetiapine", "aliases": ["seroquel"], "class": "antipsychotic", "indications": ["schizophrenia", "bipolar"], "safe_pregnancy": False, "safe_children": False},
    "olanzapine": {"name_ar": "أولانزابين", "name_en": "Olanzapine", "aliases": ["zyprexa"], "class": "antipsychotic", "indications": ["schizophrenia"], "safe_pregnancy": False, "safe_children": False},
    "risperidone": {"name_ar": "ريسبيريدون", "name_en": "Risperidone", "aliases": ["risperdal"], "class": "antipsychotic", "indications": ["schizophrenia", "autism"], "safe_pregnancy": False, "safe_children": True},
    "carbamazepine": {"name_ar": "كاربامازيبين", "name_en": "Carbamazepine", "aliases": ["tegretol"], "class": "antiepileptic", "indications": ["epilepsy", "neuralgia"], "safe_pregnancy": False, "safe_children": True},
    "valproic_acid": {"name_ar": "حمض الفالبرويك", "name_en": "Valproic Acid", "aliases": ["depakote"], "class": "antiepileptic", "indications": ["epilepsy", "bipolar"], "safe_pregnancy": False, "safe_children": True},
    "lamotrigine": {"name_ar": "لاموتريجين", "name_en": "Lamotrigine", "aliases": ["lamictal"], "class": "antiepileptic", "indications": ["epilepsy", "bipolar"], "safe_pregnancy": True, "safe_children": True},
    "levetiracetam": {"name_ar": "ليفيتيراسيتام", "name_en": "Levetiracetam", "aliases": ["keppra"], "class": "antiepileptic", "indications": ["epilepsy"], "safe_pregnancy": False, "safe_children": True},
    "gabapentin": {"name_ar": "جابابنتين", "name_en": "Gabapentin", "aliases": ["neurontin"], "class": "antiepileptic", "indications": ["neuropathy"], "safe_pregnancy": False, "safe_children": True},
    "pregabalin": {"name_ar": "بريجابالين", "name_en": "Pregabalin", "aliases": ["lyrica"], "class": "antiepileptic", "indications": ["neuropathy"], "safe_pregnancy": False, "safe_children": False},
    "valacyclovir": {"name_ar": "فالاسيكلوفير", "name_en": "Valacyclovir", "aliases": ["valtrex"], "class": "antiviral", "indications": ["herpes", "shingles"], "safe_pregnancy": True, "safe_children": True},
    "famciclovir": {"name_ar": "فامسيكلوفير", "name_en": "Famciclovir", "aliases": ["famvir"], "class": "antiviral", "indications": ["herpes"], "safe_pregnancy": True, "safe_children": False},
    "dabigatran": {"name_ar": "دابيجاتران", "name_en": "Dabigatran", "aliases": ["pradaxa"], "class": "doac", "indications": ["afib"], "safe_pregnancy": False, "safe_children": False},
    "rivaroxaban": {"name_ar": "ريفاروكسابان", "name_en": "Rivaroxaban", "aliases": ["xarelto"], "class": "doac", "indications": ["afib", "dvt"], "safe_pregnancy": False, "safe_children": False},
    "apixaban": {"name_ar": "أبيكسابان", "name_en": "Apixaban", "aliases": ["eliquis"], "class": "doac", "indications": ["afib", "dvt"], "safe_pregnancy": False, "safe_children": False},
    "prasugrel": {"name_ar": "براسوجريل", "name_en": "Prasugrel", "aliases": ["effient"], "class": "antiplatelet", "indications": ["acs"], "safe_pregnancy": False, "safe_children": False},
    "ticagrelor": {"name_ar": "تيكاجريلور", "name_en": "Ticagrelor", "aliases": ["brilinta"], "class": "antiplatelet", "indications": ["acs"], "safe_pregnancy": False, "safe_children": False},
    "ezetimibe": {"name_ar": "إيزيتيميب", "name_en": "Ezetimibe", "aliases": ["zetia"], "class": "cholesterol", "indications": ["hyperlipidemia"], "safe_pregnancy": False, "safe_children": False},
    "fenofibrate": {"name_ar": "فينوفايبرات", "name_en": "Fenofibrate", "aliases": ["tricor"], "class": "fibrate", "indications": ["hyperlipidemia"], "safe_pregnancy": False, "safe_children": False},
    "nitroglycerin": {"name_ar": "نيتروجليسرين", "name_en": "Nitroglycerin", "aliases": ["nitrostat"], "class": "nitrate", "indications": ["angina"], "safe_pregnancy": False, "safe_children": False},
    "dapagliflozin": {"name_ar": "داباجليفلوزين", "name_en": "Dapagliflozin", "aliases": ["forxiga"], "class": "sglt2", "indications": ["diabetes_type2"], "safe_pregnancy": False, "safe_children": False},
    "linagliptin": {"name_ar": "ليناجليبتين", "name_en": "Linagliptin", "aliases": ["trajenta"], "class": "dpp4", "indications": ["diabetes_type2"], "safe_pregnancy": False, "safe_children": False},
    "liraglutide": {"name_ar": "ليراجلوتيد", "name_en": "Liraglutide", "aliases": ["victoza"], "class": "glp1", "indications": ["diabetes_type2", "obesity"], "safe_pregnancy": False, "safe_children": False},
    "semaglutide": {"name_ar": "سيماجلوتيد", "name_en": "Semaglutide", "aliases": ["ozempic"], "class": "glp1", "indications": ["diabetes_type2", "obesity"], "safe_pregnancy": False, "safe_children": False},
    "formoterol": {"name_ar": "فورموتيرول", "name_en": "Formoterol", "aliases": ["foradil"], "class": "laba", "indications": ["asthma"], "safe_pregnancy": True, "safe_children": True},
    "salmeterol": {"name_ar": "سالميتيرول", "name_en": "Salmeterol", "aliases": ["serevent"], "class": "laba", "indications": ["asthma"], "safe_pregnancy": True, "safe_children": True},
    "tiotropium": {"name_ar": "تيوتروبيوم", "name_en": "Tiotropium", "aliases": ["spiriva"], "class": "lama", "indications": ["copd"], "safe_pregnancy": False, "safe_children": False},
    "ipratropium": {"name_ar": "إبراتروبيوم", "name_en": "Ipratropium", "aliases": ["atrovent"], "class": "sama", "indications": ["copd", "asthma"], "safe_pregnancy": True, "safe_children": True},
    "roflumilast": {"name_ar": "روفلوميلاست", "name_en": "Roflumilast", "aliases": ["daxas"], "class": "pde4", "indications": ["copd"], "safe_pregnancy": False, "safe_children": False},
    "montelukast": {"name_ar": "مونتيلوكاست", "name_en": "Montelukast", "aliases": ["singulair"], "class": "ltra", "indications": ["asthma"], "safe_pregnancy": True, "safe_children": True},
    "zafirlukast": {"name_ar": "زافيرلوكاست", "name_en": "Zafirlukast", "aliases": ["accolate"], "class": "ltra", "indications": ["asthma"], "safe_pregnancy": False, "safe_children": False},
    "omalizumab": {"name_ar": "أوماليزوماب", "name_en": "Omalizumab", "aliases": ["xolair"], "class": "biologic", "indications": ["asthma"], "safe_pregnancy": False, "safe_children": False},
    "etanercept": {"name_ar": "إيتانرسيبت", "name_en": "Etanercept", "aliases": ["enbrel"], "class": "biologic", "indications": ["ra", "psoriasis"], "safe_pregnancy": False, "safe_children": False},
    "adalimumab": {"name_ar": "أداليموماب", "name_en": "Adalimumab", "aliases": ["humira"], "class": "biologic", "indications": ["ra", "crohn"], "safe_pregnancy": False, "safe_children": False},
    "infliximab": {"name_ar": "إنفليكسيماب", "name_en": "Infliximab", "aliases": ["remicade"], "class": "biologic", "indications": ["ra", "crohn"], "safe_pregnancy": False, "safe_children": False},
    "rituximab": {"name_ar": "ريتوكسيماب", "name_en": "Rituximab", "aliases": ["rituxan"], "class": "biologic", "indications": ["lymphoma", "ra"], "safe_pregnancy": False, "safe_children": False},
    "trastuzumab": {"name_ar": "تراستوزوماب", "name_en": "Trastuzumab", "aliases": ["herceptin"], "class": "biologic", "indications": ["breast_cancer"], "safe_pregnancy": False, "safe_children": False},
    "bevacizumab": {"name_ar": "بيفاسيزوماب", "name_en": "Bevacizumab", "aliases": ["avastin"], "class": "biologic", "indications": ["cancer"], "safe_pregnancy": False, "safe_children": False},
    "cetuximab": {"name_ar": "سيتوكسيماب", "name_en": "Cetuximab", "aliases": ["erbitux"], "class": "biologic", "indications": ["cancer"], "safe_pregnancy": False, "safe_children": False},
}

added = 0
for k, v in NEW.items():
    if k not in drugs:
        drugs[k] = v
        added += 1

data["version"] = "3.0"
data["drugs"] = drugs
with open(DRUGS_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"\n  ✅ Added {added} drugs")
print(f"  ✅ Total: {len(drugs)}\n")
