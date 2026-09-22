# 🏥 H1-AI — مساعد الصيدلية الذكي

منصة متكاملة لإدارة الصيدليات الذكية مع AI.

## ✨ الميزات

- 🤖 مساعد ذكي (LangChain + Groq + Ollama)
- 📦 إدارة منتجات وأدوية
- 💬 WhatsApp Bot
- 📊 لوحة تحكم إدارية كاملة
- 🔒 JWT + Argon2id
- 📈 تحليلات فورية

## 🚀 التثبيت السريع

git clone <repo-url> h1-ai
cd h1-ai/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env
sudo -u postgres createdb h1ai
alembic upgrade head
uvicorn main:app --host 127.0.0.1 --port 8000

## 🔌 API الرئيسية

POST /v1/auth/login         - تسجيل دخول
POST /api/chat/message      - إرسال رسالة
GET  /v1/admin/products     - قائمة المنتجات
GET  /health                - صحة السيرفر
GET  /docs                  - Swagger UI

## 🔐 الأمان

- Argon2id للباسوردات
- JWT 30 دقيقة access + 7 أيام refresh
- Rate limiting
- RLS على الجداول الحساسة
- Audit logging كامل

## 📄 الترخيص

MIT License
