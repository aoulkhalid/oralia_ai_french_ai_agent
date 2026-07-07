# 🇫🇷 French AI Agent

> **An AI-powered conversational tutor to help learners speak French with confidence through natural conversations, instant corrections, speech recognition, and personalized learning.**

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688)
![Next.js](https://img.shields.io/badge/Next.js-Frontend-black)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue)
![Redis](https://img.shields.io/badge/Redis-Cache-red)

---

# 📖 Overview

French AI Agent ( oralia ai ) is an intelligent language-learning platform designed for French learners from **A1 to C2**.

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

- AI French Conversation (Gemini)
- Speech-to-Text (Gemini audio understanding)
- Text-to-Speech (Gemini TTS)
- Grammar Correction
- Personalized Feedback
- Conversation History
- Progress Dashboard
- Adaptive Learning
- Scenario-Based Conversations
- Exercise Generation

---

# 🏗️ Tech Stack

## Frontend

- Next.js
- React
- TypeScript

## Backend

- FastAPI
- SQLAlchemy
- Alembic
- Pydantic

## AI Services

- Google Gemini (chat, grammar correction, speech-to-text, text-to-speech)

## Database

- PostgreSQL

## Cache

- Redis

## DevOps

- Docker
- Docker Compose

---

# 📂 Project Structure

```text
french-ai-agent/

├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── services/
│   │   ├── schemas/
│   │   ├── core/
│   │   ├── database.py
│   │   └── main.py
│   │
│   ├── alembic/
│   ├── requirements.txt
│   └── .env
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── lib/
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

Create your environment files.

Backend

```bash
cp backend/.env.example backend/.env
```

Configure your Gemini API key (get one at https://aistudio.google.com/apikey):

```env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TTS_MODEL=gemini-2.5-flash-preview-tts
GEMINI_TTS_VOICE=Kore

DATABASE_URL=postgresql://postgres:postgres@localhost:5432/francais_ia
REDIS_URL=redis://localhost:6379/0

SECRET_KEY=
```

Frontend

```bash
cp frontend/.env.local.example frontend/.env.local
```

---

## Run the database + cache

```bash
docker compose up -d
```

## Run migrations

```bash
cd backend
python -m venv venv && source venv/bin/activate   # ou l'équivalent Windows
pip install -r requirements.txt
alembic upgrade head
```

## Run the backend

```bash
uvicorn app.main:app --reload
```

## Run the frontend

```bash
cd frontend
npm install
npm run dev
```

---

Backend

```
http://localhost:8000
```

Frontend

```
http://localhost:3000
```

Swagger

```
http://localhost:8000/docs
```

---

# 🗺️ Development Roadmap

---

# ✅ Phase 0 — Foundations *(Completed)*

- [x] Structure backend FastAPI / frontend Next.js
- [x] Docker Compose (PostgreSQL + Redis)
- [x] User model
- [x] Stub endpoints: `/health`, `/chat`, `/progress`
- [x] Verify that everything starts and communicates correctly
- [x] Create `.env` files and configure API keys

---

# 🗄️ Phase 1 — Complete Database

- [x] Model remaining tables: conversations, messages, corrections, progress, exercises, scenarios
- [x] Define relationships between tables
- [x] Install and configure Alembic
- [x] Generate and apply migrations

---

# 🔐 Phase 2 — Authentication & User Profile

- [x] Registration endpoint (`/auth/register`)
- [x] Login endpoint (`/auth/login`)
- [x] Password hashing
- [x] JWT authentication
- [x] `/me` endpoint
- [x] Protect routes with `get_current_user`

---

# 🤖 Phase 3 — Conversational Core (LLM)

### Implement `llm_service.py` (Gemini)

- [x] `generate_reply(message, niveau_cecrl, historique)`
- [x] `correct_message(message)`

### Tasks

- [x] Design the system prompt
- [x] Adapt conversations to CEFR level
- [x] Save conversations
- [x] Save corrections
- [x] Return conversation history
- [x] Manage conversation context

---

# 🎙️ Phase 4 — Voice (STT / TTS)

- [x] Implement `stt_service.py` (Gemini audio understanding)
- [x] Endpoint `/speech/speech-to-text`
- [x] Implement `tts_service.py` (Gemini TTS)
- [x] Endpoint `/speech/text-to-speech`
- [x] Frontend audio recording and playback

---

# 💬 Phase 5 — Chat Interface

- [x] ChatWindow component
- [x] Send messages through `/chat`
- [x] Microphone recording
- [x] Speech-to-Text integration
- [x] Audio playback
- [x] Display grammar corrections
- [x] Loading state
- [x] Network error handling

---

# 📈 Phase 6 — Progress & Statistics

- [x] Populate `progress` table
- [ ] Progress dashboard (UI)
- [ ] Charts for frequent mistakes
- [ ] CEFR progression

---

# 🚀 Phase 7 — Advanced Features

- [ ] Personalized exercise generation
- [ ] Conversation scenarios
- [ ] Automatic level adaptation
- [ ] Gamification
- [ ] Teacher mode
- [ ] DELF / TCF preparation

---

# ☁️ Phase 8 — Production & Deployment

- [ ] Redis caching
- [ ] LLM cost optimization
- [ ] Automated tests
- [ ] Structured logging
- [ ] Security
- [ ] Rate limiting
- [ ] GDPR compliance
- [ ] CI/CD
- [ ] Deployment
- [ ] Freemium / Premium monetization

---

# 📡 API

| Method | Endpoint | Description |
|----------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/auth/register` | Create an account |
| POST | `/auth/login` | Log in, get a JWT |
| GET | `/auth/me` | Current user profile |
| POST | `/chat` | Chat with the AI |
| GET | `/chat/conversations` | List conversations |
| GET | `/chat/{id}/history` | Conversation history |
| POST | `/chat/{id}/close` | Close a conversation |
| POST | `/speech/speech-to-text` | Audio → Text |
| POST | `/speech/text-to-speech` | Text → Audio |
| GET | `/progress/{user_id}` | User statistics |

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

      LLM Service   STT Service   TTS Service
       (Gemini)      (Gemini)      (Gemini)

         │             │             │

         └─────────────┼─────────────┘

                       │

                 PostgreSQL

                       │

                     Redis
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

# 👨‍💻 Author

**Khalid El Aoula**

AI Engineer

---

# ⭐ Support the Project

If you like this project, consider giving it a ⭐ on GitHub.
