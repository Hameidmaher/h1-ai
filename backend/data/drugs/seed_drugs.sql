-- ═══════════════════════════════════════════════════════════
--  H1-AI — Seed Data: 100 Common Egyptian Drugs
--  Realistic names, forms, and prices (2026)
-- ═══════════════════════════════════════════════════════════

BEGIN;

-- ─── الأدوية المسكنة والخافضة للحرارة ─────────────────────
INSERT INTO drugs (trade_name, trade_name_en, scientific_name, category, form, strength, manufacturer, prescription_required, price_egp, description) VALUES
('بنادول', 'Panadol', 'Paracetamol', 'مسكن', 'أقراص', '500mg', 'GSK', false, 25.00, 'مسكن وخافض للحرارة للألم الخفيف والمتوسط'),
('بنادول إكسترا', 'Panadol Extra', 'Paracetamol + Caffeine', 'مسكن', 'أقراص', '500mg+65mg', 'GSK', false, 35.00, 'مسكن أقوى مع كافيين للصداع'),
('بانادول أدفانس', 'Panadol Advance', 'Paracetamol', 'مسكن', 'أقراص', '500mg', 'GSK', false, 30.00, 'يُذاب بسرعة في المعدة'),
('سيتامول', 'Cetamol', 'Paracetamol', 'مسكن', 'أقراص', '500mg', 'مصر', false, 15.00, 'مسكن مصري اقتصادي'),
('إيبوبروفين', 'Ibuprofen', 'Ibuprofen', 'مضاد التهاب', 'أقراص', '400mg', 'متنوع', false, 20.00, 'مضاد التهاب غير ستيرويدي'),
('بروفين', 'Brufen', 'Ibuprofen', 'مضاد التهاب', 'أقراص', '400mg', 'Abbott', false, 45.00, 'مسكن ومضاد التهاب قوي'),
('فولتارين', 'Voltaren', 'Diclofenac Sodium', 'مضاد التهاب', 'أقراص', '50mg', 'Novartis', true, 65.00, 'مضاد التهاب وآلام المفاصل'),
('فولتارين جل', 'Voltaren Emulgel', 'Diclofenac', 'مضاد التهاب', 'جل', '1%', 'Novartis', false, 85.00, 'جل موضعي لآلام العضلات والمفاصل'),
('أسبرين بروتكت', 'Aspirin Protect', 'Acetylsalicylic Acid', 'مضاد تجلط', 'أقراص', '100mg', 'Bayer', false, 50.00, 'مانع تجلط للقلب'),
('كيتوفان', 'Ketofan', 'Ketoprofen', 'مسكن', 'أقراص', '50mg', 'Amoun', true, 40.00, 'مسكن قوي للآلام المتوسطة والشديدة');

-- ─── أدوية البرد والإنفلونزا ─────────────────────────────
INSERT INTO drugs (trade_name, trade_name_en, scientific_name, category, form, strength, manufacturer, prescription_required, price_egp, description) VALUES
('كونجستال', 'Congestal', 'Paracetamol + Pseudoephedrine + Chlorpheniramine', 'برد', 'أقراص', '500mg', 'Amoun', false, 30.00, 'للبرد والرشح والاحتقان'),
('تلفاست', 'Telfast', 'Fexofenadine', 'حساسية', 'أقراص', '180mg', 'Sanofi', false, 75.00, 'مضاد هيستامين بدون نعاس'),
('كلاريتين', 'Claritine', 'Loratadine', 'حساسية', 'أقراص', '10mg', 'Bayer', false, 55.00, 'مضاد هيستامين للحساسية الموسمية'),
('زيرتك', 'Zyrtec', 'Cetirizine', 'حساسية', 'أقراص', '10mg', 'UCB', false, 45.00, 'حساسية مع نعاس خفيف'),
('أريوس', 'Aerius', 'Desloratadine', 'حساسية', 'أقراص', '5mg', 'MSD', false, 80.00, 'حساسية بدون نعاس'),
('فلوموكس', 'Flumox', 'Amoxicillin + Clavulanic Acid', 'مضاد حيوي', 'كبسولات', '500mg+125mg', 'Hikma', true, 90.00, 'مضاد حيوي واسع المدى'),
('أوجمنتين', 'Augmentin', 'Amoxicillin + Clavulanic Acid', 'مضاد حيوي', 'أقراص', '1g', 'GSK', true, 140.00, 'مضاد حيوي من الأقوى'),
('زيثروماكس', 'Zithromax', 'Azithromycin', 'مضاد حيوي', 'أقراص', '500mg', 'Pfizer', true, 120.00, 'مضاد حيوي للجهاز التنفسي'),
('كورسيف', 'Korsif', 'Cefixime', 'مضاد حيوي', 'أقراص', '400mg', 'Hikma', true, 95.00, 'سيفالوسبورين للجهاز البولي والتنفسي'),
('سبروفلوكساسين', 'Sprofloxacin', 'Ciprofloxacin', 'مضاد حيوي', 'أقراص', '500mg', 'Amoun', true, 60.00, 'مضاد حيوي للالتهابات البولية');

-- ─── أدوية الجهاز الهضمي ─────────────────────────────────
INSERT INTO drugs (trade_name, trade_name_en, scientific_name, category, form, strength, manufacturer, prescription_required, price_egp, description) VALUES
('نيكسيوم', 'Nexium', 'Esomeprazole', 'قرحة معدة', 'كبسولات', '40mg', 'AstraZeneca', true, 130.00, 'مثبط مضخة البروتون للارتجاع'),
('لوسك', 'Losec', 'Omeprazole', 'قرحة معدة', 'كبسولات', '20mg', 'AstraZeneca', true, 85.00, 'للقرحة والارتجاع'),
('أنتودين', 'Antodine', 'Famotidine', 'قرحة معدة', 'أقراص', '20mg', 'Amoun', false, 45.00, 'مضاد H2 للقرحة'),
('موتيليوم', 'Motilium', 'Domperidone', 'غثيان', 'أقراص', '10mg', 'Janssen', false, 50.00, 'للغثيان والقيء'),
('بوسكوبان', 'Buscopan', 'Hyoscine Butylbromide', 'مغص', 'أقراص', '10mg', 'Boehringer', false, 55.00, 'للمغص والانتفاخ'),
('فيسرالجين', 'Visceralgin', 'Tiemonium', 'مغص', 'أقراص', '50mg', 'Amoun', false, 40.00, 'للمغص المعوي'),
('زانتاك', 'Zantac', 'Ranitidine', 'قرحة معدة', 'أقراص', '150mg', 'GSK', false, 35.00, 'مضاد حموضة'),
('جافيسكون', 'Gaviscon', 'Sodium Alginate', 'حموضة', 'شراب', '500mg/10ml', 'Reckitt', false, 60.00, 'لعلاج الحموضة والارتجاع'),
('ميلانتا', 'Melanta', 'Magnesium Hydroxide + Aluminium', 'حموضة', 'شراب', '400mg/5ml', 'Amoun', false, 25.00, 'مضاد حموضة سريع'),
('كريون 25000', 'Creon 25000', 'Pancreatin', 'إنزيمات', 'كبسولات', '25000 units', 'Abbott', true, 180.00, 'إنزيمات البنكرياس');

-- ─── أدوية السكر والضغط ─────────────────────────────────
INSERT INTO drugs (trade_name, trade_name_en, scientific_name, category, form, strength, manufacturer, prescription_required, price_egp, description) VALUES
('جلوكوفاج', 'Glucophage', 'Metformin', 'سكر', 'أقراص', '500mg', 'Merck', true, 45.00, 'لعلاج السكري النوع الثاني'),
('دياميكرون', 'Diamicron', 'Gliclazide', 'سكر', 'أقراص', '80mg', 'Servier', true, 70.00, 'منشط للبنكرياس للسكري'),
('جانوفيا', 'Januvia', 'Sitagliptin', 'سكر', 'أقراص', '100mg', 'MSD', true, 250.00, 'مثبط DPP-4 للسكري'),
('لانتوس', 'Lantus', 'Insulin Glargine', 'سكر', 'حقن', '100IU/ml', 'Sanofi', true, 320.00, 'إنسولين طويل المفعول'),
('نوفورابيد', 'NovoRapid', 'Insulin Aspart', 'سكر', 'حقن', '100IU/ml', 'Novo Nordisk', true, 310.00, 'إنسولين سريع المفعول'),
('كونكور', 'Concor', 'Bisoprolol', 'ضغط', 'أقراص', '5mg', 'Merck', true, 60.00, 'حاصر بيتا للضغط'),
('كابوتن', 'Capoten', 'Captopril', 'ضغط', 'أقراص', '25mg', 'Bristol', true, 40.00, 'مثبط ACE للضغط'),
('نورفاسك', 'Norvasc', 'Amlodipine', 'ضغط', 'أقراص', '5mg', 'Pfizer', true, 65.00, 'حاصر كالسيوم للضغط'),
('كوزار', 'Cozaar', 'Losartan', 'ضغط', 'أقراص', '50mg', 'MSD', true, 80.00, 'حاصر مستقبلات الأنجيوتنسين'),
('ديوفان', 'Diovan', 'Valsartan', 'ضغط', 'أقراص', '80mg', 'Novartis', true, 95.00, 'حاصر مستقبلات الأنجيوتنسين');

-- ─── أدوية القلب والكوليسترول ────────────────────────────
INSERT INTO drugs (trade_name, trade_name_en, scientific_name, category, form, strength, manufacturer, prescription_required, price_egp, description) VALUES
('ليبيتور', 'Lipitor', 'Atorvastatin', 'كوليسترول', 'أقراص', '20mg', 'Pfizer', true, 140.00, 'ستاتين لخفض الكوليسترول'),
('كريستور', 'Crestor', 'Rosuvastatin', 'كوليسترول', 'أقراص', '10mg', 'AstraZeneca', true, 160.00, 'ستاتين قوي للكوليسترول'),
('زوكور', 'Zocor', 'Simvastatin', 'كوليسترول', 'أقراص', '20mg', 'MSD', true, 90.00, 'ستاتين للكوليسترول'),
('بلافيكس', 'Plavix', 'Clopidogrel', 'مضاد تجلط', 'أقراص', '75mg', 'Sanofi', true, 180.00, 'مانع تجلط للقلب'),
('كونكور بلوس', 'Concor Plus', 'Bisoprolol + HCTZ', 'ضغط', 'أقراص', '5mg+12.5mg', 'Merck', true, 75.00, 'ضغط مركب'),
('ديجوكسين', 'Digoxin', 'Digoxin', 'قلب', 'أقراص', '0.25mg', 'Amoun', true, 30.00, 'مقوي للقلب'),
('أميودارون', 'Amiodarone', 'Amiodarone', 'قلب', 'أقراص', '200mg', 'Sanofi', true, 85.00, 'منظم لضربات القلب'),
('إيزوبتين', 'Isoptin', 'Verapamil', 'قلب', 'أقراص', '80mg', 'Abbott', true, 60.00, 'حاصر كالسيوم للقلب'),
('كارديبن', 'Cardipin', 'Nifedipine', 'ضغط', 'أقراص', '20mg', 'Amoun', true, 55.00, 'حاصر كالسيوم للضغط'),
('إيلتوكسين', 'Eltroxin', 'Levothyroxine', 'غدة درقية', 'أقراص', '50mcg', 'GSK', true, 40.00, 'هرمون الغدة الدرقية');

-- ─── الفيتامينات والمكملات ───────────────────────────────
INSERT INTO drugs (trade_name, trade_name_en, scientific_name, category, form, strength, manufacturer, prescription_required, price_egp, description) VALUES
('سنتروم', 'Centrum', 'Multivitamins', 'فيتامينات', 'أقراص', 'Multi', 'Pfizer', false, 180.00, 'فيتامينات متعددة يومية'),
('فيتاسيد سي', 'Vitacid C', 'Vitamin C', 'فيتامينات', 'أقراص فوارة', '1000mg', 'Amoun', false, 40.00, 'فيتامين سي 1000mg'),
('ديكال ب12', 'Decal B12', 'Vitamin B12 + Calcium', 'فيتامينات', 'أقراص', 'Multi', 'Hikma', false, 65.00, 'ب12 وكالسيوم'),
('نيوروتون', 'Neuroton', 'Vitamin B Complex', 'فيتامينات', 'أقراص', 'Multi', 'Amoun', false, 55.00, 'فيتامينات ب المركبة'),
('أوميجا 3', 'Omega 3', 'Fish Oil', 'مكمل', 'كبسولات', '1000mg', 'متنوع', false, 150.00, 'زيت السمك للأوميجا 3'),
('حديد فيروجلوبين', 'Feroglobin', 'Iron + Folic Acid', 'مكمل', 'كبسولات', 'Multi', 'Vitabiotics', false, 120.00, 'حديد وفوليك للأنيميا'),
('كالسيوم دي 3', 'Calcium D3', 'Calcium + Vitamin D3', 'مكمل', 'أقراص', '500mg', 'متنوع', false, 80.00, 'كالسيوم مع فيتامين د'),
('زنك 50', 'Zinc 50', 'Zinc Gluconate', 'مكمل', 'أقراص', '50mg', 'متنوع', false, 70.00, 'زنك للمناعة'),
('فوليك أسيد', 'Folic Acid', 'Folic Acid', 'فيتامينات', 'أقراص', '5mg', 'متنوع', false, 20.00, 'حمض الفوليك للحوامل'),
('فيتامين د 50000', 'Vitamin D 50000', 'Cholecalciferol', 'فيتامينات', 'كبسولات', '50000IU', 'متنوع', true, 90.00, 'فيتامين د جرعة أسبوعية');

-- ─── المضادات الحيوية والمطهرات ─────────────────────────
INSERT INTO drugs (trade_name, trade_name_en, scientific_name, category, form, strength, manufacturer, prescription_required, price_egp, description) VALUES
('فلاجيل', 'Flagyl', 'Metronidazole', 'مضاد حيوي', 'أقراص', '500mg', 'Sanofi', true, 35.00, 'مضاد للطفيليات والبكتيريا اللاهوائية'),
('دانترول', 'Dantrolene', 'Nitrofurantoin', 'مضاد حيوي', 'كبسولات', '100mg', 'Amoun', true, 55.00, 'مضاد حيوي للمسالك البولية'),
('سيفوتاكس', 'Cefotax', 'Cefotaxime', 'مضاد حيوي', 'حقن', '1g', 'Amoun', true, 70.00, 'سيفالوسبورين للحقن'),
('لوسيد', 'Lucid', 'Clarithromycin', 'مضاد حيوي', 'أقراص', '500mg', 'Abbott', true, 130.00, 'ماكروليد للجهاز التنفسي'),
('تافانيك', 'Tavanic', 'Levofloxacin', 'مضاد حيوي', 'أقراص', '500mg', 'Sanofi', true, 150.00, 'فلوروكينولون للالتهابات'),
('بيتادين', 'Betadine', 'Povidone Iodine', 'مطهر', 'محلول', '10%', 'Mundipharma', false, 45.00, 'مطهر للجروح'),
('ريفو', 'Rivo', 'Povidone Iodine', 'مطهر', 'غسول', '7.5%', 'Amoun', false, 35.00, 'غسول مطهر'),
('ميكوسيستاتين', 'Mycostatin', 'Nystatin', 'مضاد فطري', 'قطرة فم', '100000IU/ml', 'Bristol', true, 55.00, 'مضاد فطريات للفم'),
('ديفلوكان', 'Diflucan', 'Fluconazole', 'مضاد فطري', 'كبسولات', '150mg', 'Pfizer', true, 90.00, 'مضاد فطريات للفطريات النسائية'),
('لاميزيل', 'Lamisil', 'Terbinafine', 'مضاد فطري', 'كريم', '1%', 'Novartis', false, 70.00, 'كريم للفطريات الجلدية');

-- ─── أدوية أخرى شائعة ────────────────────────────────────
INSERT INTO drugs (trade_name, trade_name_en, scientific_name, category, form, strength, manufacturer, prescription_required, price_egp, description) VALUES
('فياجرا', 'Viagra', 'Sildenafil', 'ضعف جنسي', 'أقراص', '50mg', 'Pfizer', true, 200.00, 'لعلاج ضعف الانتصاب'),
('بروبيشيا', 'Propecia', 'Finasteride', 'تساقط شعر', 'أقراص', '1mg', 'MSD', true, 250.00, 'لتساقط الشعر عند الرجال'),
('روأكيوتان', 'Roaccutane', 'Isotretinoin', 'حبوب شباب', 'كبسولات', '20mg', 'Roche', true, 350.00, 'لعلاج حب الشباب الشديد'),
('بريجابالين', 'Pregabalin', 'Pregabalin', 'أعصاب', 'كبسولات', '75mg', 'Pfizer', true, 120.00, 'للألم العصبي والصرع'),
('جاراسين', 'Jarasin', 'Escitalopram', 'اكتئاب', 'أقراص', '10mg', 'Lundbeck', true, 130.00, 'مضاد اكتئاب SSRI'),
('زولوفت', 'Zoloft', 'Sertraline', 'اكتئاب', 'أقراص', '50mg', 'Pfizer', true, 110.00, 'مضاد اكتئاب SSRI'),
('ريفوتريل', 'Rivotril', 'Clonazepam', 'قلق', 'أقراص', '2mg', 'Roche', true, 60.00, 'بنزوديازيبين للقلق'),
('زاناكس', 'Xanax', 'Alprazolam', 'قلق', 'أقراص', '0.5mg', 'Pfizer', true, 80.00, 'بنزوديازيبين للقلق'),
('إيميجران', 'Imigran', 'Sumatriptan', 'صداع نصفي', 'أقراص', '50mg', 'GSK', true, 180.00, 'لعلاج الصداع النصفي'),
('أليرت', 'Alert', 'Fexofenadine', 'حساسية', 'أقراص', '120mg', 'Amoun', false, 65.00, 'حساسية بدون نعاس');

COMMIT;

-- ═══════════════════════════════════════════════════════════
--  تحقق
-- ═══════════════════════════════════════════════════════════
DO $$
DECLARE
    total INT;
BEGIN
    SELECT COUNT(*) INTO total FROM drugs;
    RAISE NOTICE '✅ Seed: % دواء في الجدول', total;
END $$;

