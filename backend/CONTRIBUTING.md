# 🤝 دليل المساهمة

## الإعداد

git clone <repo>
cd h1-ai/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

## العملية

1. Fork المستودع
2. git checkout -b feature/xyz
3. اكتب كود + tests
4. pytest
5. git commit -m "feat: add xyz"
6. Push + افتح PR

## معايير Commit

- feat: ميزة جديدة
- fix: إصلاح خطأ
- docs: توثيق
- chore: صيانة
- refactor: إعادة هيكلة
- test: اختبارات
- security: تحسينات أمنية
