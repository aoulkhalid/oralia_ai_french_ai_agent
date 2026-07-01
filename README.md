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

French AI Agent is an intelligent language-learning platform designed for French learners from **A1 to C2**.

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

- AI French Conversation
- Speech-to-Text (Whisper)
- Text-to-Speech
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
- TailwindCSS

## Backend

- FastAPI
- SQLAlchemy
- Alembic
- Pydantic

## AI Services

- OpenAI GPT
- Anthropic Claude (optional)
- Whisper
- OpenAI TTS / ElevenLabs

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
│   ├── public/
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
cp .env.example .env
```

Configure your API keys.

```env
OPENAI_API_KEY=

ANTHROPIC_API_KEY=

ELEVENLABS_API_KEY=

DATABASE_URL=

REDIS_URL=

JWT_SECRET=
```

---

## Run with Docker

```bash
docker compose up --build
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

- [ ] Model remaining tables: conversations, messages, corrections, progress, exercises, scenarios
- [ ] Define relationships between tables
- [ ] Install and configure Alembic
- [ ] Generate and apply migrations

---

# 🔐 Phase 2 — Authentication & User Profile

- [ ] Registration endpoint (`/auth/register`)
- [ ] Login endpoint (`/auth/login`)
- [ ] Password hashing
- [ ] JWT authentication
- [ ] `/me` endpoint
- [ ] Protect routes with `get_current_user`

---

# 🤖 Phase 3 — Conversational Core (LLM)

### Implement `llm_service.py`

- [ ] `generate_reply(message, niveau_cecrl, historique)`
- [ ] `correct_message(message)`

### Tasks

- [ ] Design the system prompt
- [ ] Adapt conversations to CEFR level
- [ ] Save conversations
- [ ] Save corrections
- [ ] Return conversation history
- [ ] Manage conversation context

---

# 🎙️ Phase 4 — Voice (STT / TTS)

- [ ] Implement `stt_service.py`
- [ ] Endpoint `/speech-to-text`
- [ ] Implement `tts_service.py`
- [ ] Endpoint `/text-to-speech`
- [ ] Frontend audio recording and playback

---

# 💬 Phase 5 — Chat Interface

- [ ] ChatWindow component
- [ ] Send messages through `/chat`
- [ ] Microphone recording
- [ ] Speech-to-Text integration
- [ ] Audio playback
- [ ] Display grammar corrections
- [ ] Loading state
- [ ] Network error handling

---

# 📈 Phase 6 — Progress & Statistics

- [ ] Compute learning statistics
- [ ] Populate `progress` table
- [ ] Progress dashboard
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
| POST | `/chat` | Chat with the AI |
| POST | `/speech-to-text` | Audio → Text |
| POST | `/text-to-speech` | Text → Audio |
| GET | `/progress` | User statistics |
| POST | `/exercise` | Generate exercises |

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
