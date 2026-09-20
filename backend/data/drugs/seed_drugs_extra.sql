BEGIN;

INSERT INTO drugs (trade_name, trade_name_en, scientific_name, category, form, strength, manufacturer, prescription_required, price_egp, description) VALUES
-- مسكنات إضافية
('كاتافلام', 'Cataflam', 'Diclofenac Potassium', 'مضاد التهاب', 'أقراص', '50mg', 'Novartis', true, 55.00, 'مسكن سريع المفعول'),
('موبيك', 'Mobic', 'Meloxicam', 'مضاد التهاب', 'أقراص', '15mg', 'Boehringer', true, 85.00, 'مضاد التهاب لآلام المفاصل'),
('سيليكوكسيب', 'Celebrex', 'Celecoxib', 'مضاد التهاب', 'كبسولات', '200mg', 'Pfizer', true, 150.00, 'مضاد التهاب COX-2'),
('نابروكسين', 'Naproxen', 'Naproxen', 'مضاد التهاب', 'أقراص', '500mg', 'Roche', true, 60.00, 'مسكن طويل المفعول'),
-- أدوية برد إضافية
('فلوتاب', 'Flutab', 'Paracetamol + Phenylephrine', 'برد', 'كبسولات', '500mg', 'Amoun', false, 35.00, 'للبرد بدون نعاس'),
('رينوستوب', 'Rhinostop', 'Xylometazoline', 'احتقان أنف', 'بخاخ', '0.1%', 'Novartis', false, 45.00, 'بخاخ للاحتقان الأنفي'),
('أوتريفين', 'Otrivin', 'Xylometazoline', 'احتقان أنف', 'قطرة أنف', '0.05%', 'GSK', false, 40.00, 'قطرة للأنف'),
-- أدوية معدة إضافية
('بارييت', 'Pariet', 'Rabeprazole', 'قرحة معدة', 'أقراص', '20mg', 'Janssen', true, 120.00, 'مثبط مضخة بروتون'),
('كونترولوك', 'Controloc', 'Pantoprazole', 'قرحة معدة', 'أقراص', '40mg', 'Takeda', true, 95.00, 'للقرحة والارتجاع'),
('موتيليوم شراب', 'Motilium Suspension', 'Domperidone', 'غثيان', 'شراب', '1mg/ml', 'Janssen', false, 55.00, 'شراب للغثيان للأطفال'),
-- أدوية ضغط إضافية
('ميكارديس', 'Micardis', 'Telmisartan', 'ضغط', 'أقراص', '40mg', 'Boehringer', true, 110.00, 'حاصر مستقبلات أنجيوتنسين'),
('إكسفورج', 'Exforge', 'Amlodipine + Valsartan', 'ضغط', 'أقراص', '5mg+80mg', 'Novartis', true, 160.00, 'ضغط مركب قوي'),
('كارفيديلول', 'Carvidelol', 'Carvedilol', 'ضغط', 'أقراص', '12.5mg', 'Roche', true, 75.00, 'حاصر بيتا و ألفا'),
-- أدوية سكر إضافية
('فورسيجا', 'Forxiga', 'Dapagliflozin', 'سكر', 'أقراص', '10mg', 'AstraZeneca', true, 280.00, 'مثبط SGLT2 للسكري'),
('تروليسيتي', 'Trulicity', 'Dulaglutide', 'سكر', 'حقن', '1.5mg', 'Lilly', true, 650.00, 'GLP-1 أسبوعي للسكري'),
-- أدوية أخرى
('لوراتادين', 'Loratadine', 'Loratadine', 'حساسية', 'أقراص', '10mg', 'Amoun', false, 35.00, 'حساسية اقتصادي'),
('مونتيلوكاست', 'Montelukast', 'Montelukast', 'ربو', 'أقراص', '10mg', 'MSD', true, 130.00, 'للربو والحساسية'),
('فنتولين', 'Ventolin', 'Salbutamol', 'ربو', 'بخاخ', '100mcg', 'GSK', false, 90.00, 'بخاخ للربو'),
('سيمبيكورت', 'Symbicort', 'Budesonide + Formoterol', 'ربو', 'بخاخ', '160/4.5', 'AstraZeneca', true, 220.00, 'بخاخ مركب للربو'),
('أوجمنتين شراب', 'Augmentin Suspension', 'Amoxicillin + Clavulanic Acid', 'مضاد حيوي', 'شراب', '457mg/5ml', 'GSK', true, 110.00, 'مضاد حيوي للأطفال');

COMMIT;

DO $$
DECLARE total INT;
BEGIN
    SELECT COUNT(*) INTO total FROM drugs;
    RAISE NOTICE '✅ Seed extra: % دواء إجمالي', total;
END $$;
