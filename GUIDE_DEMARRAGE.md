# Guide de démarrage — Agent IA Apprentissage du Français

Ce guide détaille **toutes les étapes** pour faire tourner le projet en local
(backend FastAPI + frontend Next.js + PostgreSQL + Redis), avec **Groq (gratuit) comme LLM par défaut**
comme unique modèle IA.

---

## 0. Prérequis

Avant de commencer, installez :

- **Python** 3.12 (`python3 --version`)
- **Node.js** 20+ et **npm** (`node -v`, `npm -v`)
- **Docker** et **Docker Compose** (`docker -v`, `docker compose version`)
- **Git**
- Une clé API Groq (gratuite) : https://console.groq.com/keys

---

## 1. Cloner le projet

```bash
git clone <url-du-repo>
cd oralia_ai_french_ai_agent
```

---

## Option A — Tout lancer avec Docker Compose (recommandé)

```bash
cp backend/.env.example backend/.env
# Éditez backend/.env : remplissez au minimum LLM_API_KEY et JWT_SECRET_KEY

docker compose up --build
```

Docker Compose démarre, dans l'ordre (via des healthchecks) :
`postgres` → `redis` → `backend` (applique automatiquement `alembic upgrade
head` puis lance l'API) → `frontend`.

- Frontend : http://localhost:3000
- Backend : http://localhost:8000
- Swagger : http://localhost:8000/docs
- Health check complet (DB + Redis) : http://localhost:8000/health/full

Pour arrêter : `Ctrl+C` puis `docker compose down` (ajoutez `-v` pour
supprimer aussi les données PostgreSQL).

---

## Option B — Lancer chaque service manuellement

### 1. Lancer PostgreSQL + Redis

```bash
docker compose up -d postgres redis
docker ps   # vous devez voir 2 conteneurs actifs (postgres, redis)
```

### 2. Configurer et lancer le Backend (FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

pip install -r requirements.txt
cp .env.example .env
```

Éditez `.env` et remplissez au minimum :

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/francais_ia
REDIS_URL=redis://localhost:6379/0

JWT_SECRET_KEY=<générez avec: python -c "import secrets; print(secrets.token_urlsafe(32))">
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

LLM_API_KEY=<votre clé Groq>
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.3-70b-versatile
```

> ⚠️ Sans `LLM_API_KEY`, les endpoints `/chat` renverront une erreur
> 503 propre (le reste de l'application — auth, historique, progression —
> fonctionne indépendamment).

Appliquez les migrations puis lancez le serveur :

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

Vérifiez :

```bash
curl http://localhost:8000/health
# {"status": "ok"}

curl http://localhost:8000/health/full
# {"status": "ok", "database": "ok", "redis": "ok"}
```

### 3. Configurer et lancer le Frontend (Next.js)

Dans un **nouveau terminal** :

```bash
cd frontend
npm install
cp .env.local.example .env.local   # doit contenir NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

- App disponible sur : **http://localhost:3000**

Si la page d'accueil affiche "Backend injoignable ❌", vérifiez que :
- le backend tourne bien sur le port 8000 ;
- `CORS_ORIGINS` (dans `backend/.env`) inclut bien `http://localhost:3000`.

---

## Récapitulatif — relancer le projet au quotidien

```bash
# Terminal 1 — bases de données
docker compose up -d postgres redis

# Terminal 2 — backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 3 — frontend
cd frontend && npm run dev
```

---

## État actuel du projet

Toutes les fonctionnalités listées dans le README sont implémentées et
testées de bout en bout (inscription, connexion, chat via Groq/LLM compatible OpenAI avec
historique et correction grammaticale, transcription audio, synthèse
vocale, tableau de progression, migrations Alembic à jour avec les
modèles SQLAlchemy).

Restent volontairement hors scope (voir README, phases 6-8) : dashboard de
progression graphique côté UI, génération d'exercices personnalisés,
scénarios de conversation, tests automatisés, CI/CD.

---

## Dépannage rapide

| Problème | Solution |
|---|---|
| `psycopg2` erreur d'installation | Installer `libpq-dev` (Linux) — `psycopg2-binary` dans requirements.txt suffit sur la plupart des systèmes |
| Port 5432/6379 déjà utilisé | Arrêter un PostgreSQL/Redis local existant, ou changer les ports dans `docker-compose.yml` |
| Port 8000 déjà utilisé | `uvicorn app.main:app --reload --port 8001` (et adapter `NEXT_PUBLIC_API_URL`) |
| `ModuleNotFoundError` côté backend | Vérifier que le venv est bien activé avant `pip install` |
| CORS bloqué | Vérifier `CORS_ORIGINS` dans `backend/.env` |
| `/chat` renvoie 503 | Vérifiez `LLM_API_KEY` dans `backend/.env` et que `LLM_BASE_URL` est bien joignable depuis le serveur (par défaut api.groq.com) |
| Transcription audio lente au premier essai | Normal : `faster-whisper` télécharge le modèle Whisper (`STT_MODEL_SIZE`) lors du tout premier appel, puis le met en cache |
| `alembic upgrade head` échoue | Vérifiez que PostgreSQL est bien démarré et que `DATABASE_URL` pointe vers la bonne base |
