# 🇫🇷 French AI Agent

> **An AI-powered conversational tutor to help learners speak French with confidence through natural conversations, instant corrections, speech recognition, and personalized learning.**

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688)
![Next.js](https://img.shields.io/badge/Next.js-Frontend-black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue)
![Redis](https://img.shields.io/badge/Redis-Cache-red)
![Groq](https://img.shields.io/badge/LLM-Groq-orange)

---

# 📖 Overview

French AI Agent (oralia ai) is an intelligent language-learning platform designed for French learners from **A1 to C2**.

Unlike traditional language-learning applications, French AI Agent allows users to practice real conversations with an AI tutor that:

- 💬 Holds natural conversations
- 📝 Corrects grammar mistakes
- 🧠 Explains errors pedagogically
- 🎤 Understands spoken French
- 🔊 Speaks back naturally
- 📊 Tracks learning progress
- 🎯 Adapts to each learner's CEFR level

---

# ✨ Features

- AI French Conversation ([Groq](https://console.groq.com), `llama-3.3-70b-versatile` — or any OpenAI-compatible provider: DeepSeek, Ollama, etc.)
- Speech-to-Text (local, [faster-whisper](https://github.com/SYSTRAN/faster-whisper), no API key)
- Text-to-Speech ([edge-tts](https://github.com/rany2/edge-tts), free, no API key)
- Grammar Correction
- Personalized Feedback
- Conversation History
- Progress Dashboard
- Adaptive Learning
- Scenario-Based Conversations
- Exercise Generation
- Rate limiting (Redis) to protect the LLM API from abuse
- Personalized exercise generation targeting your most frequent mistakes
- Gamification (points, daily streaks, badges)
- Teacher mode (view any student's progress dashboard)
- Automatic CEFR level-up based on recent performance
- LLM response caching (Redis) to reduce API costs
- GDPR data export & account deletion endpoints
- Automated test suite (pytest) + CI (GitHub Actions)

---

# 🏗️ Tech Stack

## Frontend

- Next.js 14 (App Router, standalone Docker output)
- React 18
- TypeScript

## Backend

- FastAPI
- SQLAlchemy 2.0
- Alembic
- Pydantic v2 / pydantic-settings

## AI Services

- **Groq** (`llama-3.3-70b-versatile`, free tier) by default, via the OpenAI-compatible SDK — chat + grammar correction. Swappable for DeepSeek, Ollama, or any OpenAI-compatible endpoint via `.env`.
- **faster-whisper** (local, offline) — speech-to-text
- **edge-tts** (free, no key) — text-to-speech

> Google Gemini has been fully removed from this project. All text generation
> now goes through an OpenAI-compatible LLM (Groq by default). Gemini does not support audio, so
> STT/TTS were migrated to open-source, key-free alternatives instead of a
> second paid vendor.

## Database

- PostgreSQL 16

## Cache / Rate limiting

- Redis 7

## DevOps

- Docker
- Docker Compose (postgres + redis + backend + frontend, with healthchecks)

---

# 📂 Project Structure

```text
oralia_ai_french_ai_agent/

├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── services/
│   │   │   ├── llm_service.py   # chat + correction (LLM, Groq by default)
│   │   │   ├── stt_service.py        # speech-to-text (faster-whisper)
│   │   │   ├── tts_service.py        # text-to-speech (edge-tts)
│   │   │   └── conversation_service.py
│   │   ├── schemas/
│   │   ├── core/
│   │   │   ├── config.py             # centralized Settings (pydantic-settings)
│   │   │   ├── security.py           # JWT + bcrypt
│   │   │   ├── deps.py               # get_current_user
│   │   │   └── redis_client.py       # Redis client + rate limiter
│   │   ├── database.py
│   │   └── main.py
│   │
│   ├── alembic/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   └── .env                          # gitignored, never commit real secrets
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
│   ├── Dockerfile
│   ├── next.config.js
│   └── package.json
│
├── docker-compose.yml
├── README.md
└── LICENSE
```

---

# 🚀 Getting Started

## Clone the repository

```bash
git clone https://github.com/your-username/french-ai-agent.git
cd french-ai-agent
```

---

## Environment Variables

### Backend

```bash
cp backend/.env.example backend/.env
```

Then edit `backend/.env` and fill in:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/francais_ia
REDIS_URL=redis://localhost:6379/0

JWT_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

LLM_API_KEY=<your Groq key from https://console.groq.com/keys>
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile

CORS_ORIGINS=http://localhost:3000
```

⚠️ **Security note**: never commit `backend/.env`. It is already listed in
`.gitignore`. If a real API key or JWT secret was ever committed to this
repository or shared outside your team, **rotate/revoke it immediately**
from the relevant provider dashboard before using this project further.

### Frontend

```bash
cp frontend/.env.local.example frontend/.env.local
```

---

## Option A — Run everything with Docker Compose (recommended)

```bash
docker compose up --build
```

This starts, in order (via healthchecks): `postgres` → `redis` → `backend`
(runs `alembic upgrade head` automatically, then serves the API) →
`frontend`.

- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Backend readiness check: http://localhost:8000/health/full

## Option B — Run services locally

```bash
docker compose up -d postgres redis
```

```bash
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

```bash
cd frontend
npm install
npm run dev
```

---

# 📡 API

| Method | Endpoint | Description |
|----------|----------|-------------|
| GET | `/health` | Liveness check |
| GET | `/health/full` | Readiness check (DB + Redis) |
| POST | `/auth/register` | Create an account |
| POST | `/auth/login` | Log in, get a JWT |
| GET | `/auth/me` | Current user profile |
| POST | `/chat` | Chat with the AI (rate-limited) |
| GET | `/chat/conversations` | List conversations |
| GET | `/chat/{id}/history` | Conversation history |
| POST | `/chat/{id}/close` | Close a conversation |
| POST | `/speech/speech-to-text` | Audio → Text (rate-limited) |
| POST | `/speech/text-to-speech` | Text → Audio (rate-limited) |
| GET | `/progress/{user_id}` | User statistics |
| GET | `/progress/{user_id}/dashboard` | Full dashboard: level, points, streak, badges, trends |
| GET | `/scenarios` | List conversation scenarios (filter by `categorie`/`niveau_cecrl`) |
| POST | `/exercises/generate` | Generate a personalized exercise |
| POST | `/exercises/{id}/submit` | Submit an answer, get feedback |
| GET | `/teacher/students` | List all students (teacher accounts only) |
| GET | `/teacher/students/{id}/dashboard` | A specific student's dashboard (teacher only) |
| GET / POST | `/billing/plan`, `/billing/upgrade` | Freemium/premium scaffold (see `DEPLOYMENT.md`) |
| GET | `/auth/me/data-export` | GDPR data export |
| DELETE | `/auth/me` | GDPR account deletion |

---

# 📊 Architecture

```text
                Frontend (Next.js)
                       │
                 REST API
                       │
                FastAPI Backend
         ┌─────────────┼─────────────┐
         │             │             │
   LLM Service       STT Service   TTS Service
   (Groq/llama-3.3)  (faster-whisper) (edge-tts)
         │             │             │
         └─────────────┼─────────────┘
                       │
              PostgreSQL + Redis
```

---

# 🎯 Target Users

- Students
- Professionals
- Job seekers
- Immigrants
- Self-learners
- DELF / TCF candidates

---

# 📜 License

MIT License

---

# 🧪 Testing

```bash
cd backend
pip install -r requirements-dev.txt
pytest -v --cov=app
```

Tests run against an in-memory SQLite database (see `tests/conftest.py`) —
no real PostgreSQL/Redis needed. The LLM is mocked in every test.

---

# 🚢 Deployment & CI

- `.github/workflows/ci.yml` runs the test suite + frontend build + Docker
  image builds on every push/PR.
- See `DEPLOYMENT.md` for concrete production deployment options
  (Railway, Render, Fly.io, VPS + Caddy) and a pre-launch checklist.
- `docker-compose.prod.yml` is the production variant of
  `docker-compose.yml` (no exposed DB ports, `restart: always`, JSON logs).

---

# ⚠️ Known limitations / scaffolds (honest disclosure)

A few Phase 7/8 features are real, tested, working code, but with
deliberate scope limits — read `DEPLOYMENT.md` and the comments in the
files below before relying on them in production:

- **Teacher mode** (`app/routers/teacher.py`): no classroom concept yet —
  a "teacher" account sees *all* students. Promote an account manually:
  `UPDATE users SET role = 'teacher' WHERE email = '...';`
- **Freemium/premium** (`app/routers/billing.py`): `plan` field and
  rate-limit differentiation are real, but `/billing/upgrade` is a
  demo toggle, **not** a real payment integration. Wire up Stripe (or
  similar) before charging real users — see comments in that file.
- **GDPR** (`app/routers/auth.py` — data export & deletion): the technical
  mechanisms are implemented; full legal compliance also requires a
  published privacy policy, a data processing register, and a documented
  legal basis per data use, which are outside the scope of code.

---

# 👨‍💻 Author

**Khalid El Aoula**

AI Engineer
