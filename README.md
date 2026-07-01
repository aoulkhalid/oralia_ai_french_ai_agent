# Agent IA - Apprentissage du Français

Squelette de projet (Étape 1) : backend FastAPI + frontend Next.js + PostgreSQL/Redis.

## Démarrage rapide

### 1. Lancer PostgreSQL et Redis
```bash
docker-compose up -d
```

### 2. Backend (FastAPI)
```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows : venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # puis remplir les clés API
uvicorn app.main:app --reload
```
→ API disponible sur http://localhost:8000
→ Documentation interactive : http://localhost:8000/docs

### 3. Frontend (Next.js)
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```
→ App disponible sur http://localhost:3000

## Structure du projet

```
francais-ia/
├── backend/
│   ├── app/
│   │   ├── main.py          # point d'entrée FastAPI
│   │   ├── database.py      # config SQLAlchemy
│   │   ├── models/          # modèles de données (users, ...)
│   │   ├── routers/         # endpoints (health, chat, progress)
│   │   └── services/        # logique métier (llm, stt, tts)
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── app/                 # pages Next.js (App Router)
│   ├── components/          # composants React
│   ├── package.json
│   └── .env.local.example
├── docker-compose.yml       # PostgreSQL + Redis
└── README.md
```

## Prochaines étapes

1. Vérifier que le frontend affiche "Backend OK ✅" (connexion validée)
2. Ajouter les tables `conversations`, `messages`, `corrections`, `progress`, `exercises`, `scenarios`
3. Implémenter `llm_service.py` (connexion à l'API du LLM)
4. Implémenter `stt_service.py` (Whisper) et `tts_service.py`
5. Construire l'interface de chat vocal (`ChatWindow.tsx`)
