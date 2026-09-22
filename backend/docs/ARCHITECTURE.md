# 🏗️ معمارية H1-AI

Internet
  ↓
Nginx (80/443)  ← reverse proxy
  ↓
h1ai-api (127.0.0.1:8000)  ← FastAPI
  ├─ Auth
  ├─ Admin routes
  ├─ Chat API
  └─ WebSocket
  ↓
PostgreSQL 17 + Redis

## Stack

| المكون | التقنية |
|---|---|
| Backend | FastAPI 0.141 + Uvicorn |
| DB | PostgreSQL 17 + SQLAlchemy 2.0 |
| Auth | JWT + Argon2id |
| LLM | Groq + Ollama + LangChain |
| Frontend | Vanilla JS + PWA |
| Proxy | Nginx |
| Monitoring | Grafana + Prometheus + Loki |
