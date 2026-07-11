# Guide de test complet — Agent IA Apprentissage Français

## 0. Prérequis : vérifier que tout tourne

```bash
cd ~/projects/oralia_ai_french_ai_agent
docker compose ps
```
Tu dois voir `postgres` et `redis` avec le statut `Up`. Sinon :
```bash
docker compose up -d
```

Dans un terminal séparé, active le venv et lance le serveur :
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Dans un **autre** terminal, teste que le serveur répond :
```bash
curl http://127.0.0.1:8000/health
```
Réponse attendue : `{"status":"ok"}`. Si ça ne répond pas, le serveur a crashé — regarde le traceback dans le terminal uvicorn avant de continuer.

---

## 1. Tester l'inscription (`POST /auth/register`)

```bash
curl -i -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "khalid.ela@example.com",
    "password": "Khalid@123",
    "nom": "Khalid Ela",
    "niveau_cecrl": "B1"
  }'
```

- **Attendu** : `201 Created` + objet utilisateur (id, email, nom, niveau_cecrl, is_active, created_at) — **sans** le mot de passe.
- Si tu relances exactement la même commande une 2e fois : attendu `400` ou `409` (email déjà utilisé), **pas** `500`.

Vérifie en base :
```bash
docker exec -it $(docker ps -qf "name=postgres") psql -U postgres -d francais_ia \
  -c "SELECT id, email, nom, niveau_cecrl, is_active FROM users;"
```

---

## 2. Tester la connexion (`POST /auth/login`)

Cet endpoint utilise le format OAuth2 (form-urlencoded, pas JSON) :

```bash
curl -i -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&username=khalid.ela@example.com&password=Khalid@123"
```

Points clés :
- `grant_type` doit être **exactement** `password`
- `username` = l'**email** (pas le nom affiché)
- pas besoin de `scope`, `client_id`, `client_secret`

**Attendu** : `200` avec :
```json
{"access_token": "xxxxxxx", "token_type": "bearer"}
```

**Sauvegarde le token** dans une variable pour la suite :
```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&username=khalid.ela@example.com&password=Khalid@123" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo $TOKEN
```
Si `$TOKEN` est vide, le login a échoué — vérifie la réponse brute d'abord.

Teste aussi le cas d'erreur (mauvais mot de passe) :
```bash
curl -i -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password&username=khalid.ela@example.com&password=MauvaisMdp"
```
**Attendu** : `401 Unauthorized`.

---

## 3. Vérifier le schéma exact de chaque endpoint restant

⚠️ Important : ton code local (`chat.py`, `progress.py`, un futur `speech.py`) a évolué par rapport aux fichiers du projet que j'ai sous les yeux (ces derniers montrent encore des versions placeholder sans authentification ni Gemini). Je ne peux donc pas te garantir les noms exacts des champs sans que tu regardes Swagger toi-même.

**Étape obligatoire avant de tester chaque route :**

1. Ouvre `http://127.0.0.1:8000/docs`
2. Clique sur la route à tester (ex. `POST /chat`)
3. Clique sur **"Try it out"**
4. Regarde le **schéma d'exemple** affiché (les champs requis, leurs types)
5. Regarde s'il y a un cadenas 🔒 à côté de la route → si oui, elle nécessite le token du login

Fais ça pour `chat`, `progress`, et `speech`, et note les champs exacts. Ensuite utilise les modèles de commandes ci-dessous en les adaptant.

---

## 4. Tester le chat (`POST /chat` — à adapter selon Swagger)

Modèle général si la route est protégée par token :

```bash
curl -i -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message": "Bonjour, comment ça va ?"}'
```

**Attendu** : `200` avec une réponse générée (probablement `reply` + `correction` si le champ correction existe encore).

Cas à tester :
- Message correct grammaticalement → `correction` doit être vide/null
- Message avec une faute volontaire (ex: `"Je suis allé au magasin hier et j'ai acheté des pomme"`) → vérifie que la correction détecte la faute
- Token manquant ou invalide → attendu `401`
- Corps vide `{}` → attendu `422` (erreur de validation)

Si le endpoint plante avec `500`, colle-moi le traceback complet du terminal uvicorn — je pourrai diagnostiquer précisément.

---

## 5. Tester le suivi de progression (`GET /progress/...`)

Si la route ressemble à l'ancienne version (`GET /progress/{user_id}`) :

```bash
curl -i http://127.0.0.1:8000/progress/1 \
  -H "Authorization: Bearer $TOKEN"
```

Mais si elle a évolué pour utiliser l'utilisateur connecté automatiquement (`GET /progress/me`), adapte l'URL selon ce que Swagger montre.

**Attendu** : `200` avec les stats (niveau, conversations complétées, erreurs fréquentes).

Cas à tester :
- Utilisateur avec des conversations existantes → les stats doivent refléter des vraies données (pas juste le placeholder)
- ID d'un utilisateur qui n'existe pas → `404`
- Sans token → `401`

---

## 6. Tester la voix (`speech` — STT/TTS)

C'est le plus délicat car ça implique l'upload d'un fichier audio (`multipart/form-data`), pas du JSON.

D'abord, crée un petit fichier audio de test si tu n'en as pas :
```bash
# Nécessite ffmpeg — génère 2 secondes de silence en wav
sudo apt install -y ffmpeg   # si pas déjà installé
ffmpeg -f lavfi -i anullsrc=r=16000:cl=mono -t 2 -q:a 9 test.wav
```

Puis, selon ce que Swagger montre comme nom de champ (souvent `file` ou `audio_file`) :

```bash
curl -i -X POST http://127.0.0.1:8000/speech/transcribe \
  -H "Authorization: Bearer $TOKEN" \
  -F "audio_file=@test.wav"
```

Pour le TTS (texte → audio), si la route existe :
```bash
curl -i -X POST http://127.0.0.1:8000/speech/synthesize \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"text": "Bonjour, comment allez-vous ?"}' \
  --output reponse.mp3
```
Puis écoute `reponse.mp3` pour vérifier que l'audio est correct.

⚠️ Comme pour le chat, adapte les noms de route et de champs à ce que Swagger affiche réellement — je te donne le squelette, pas les noms exacts.

---

## 7. Checklist résumée

| Étape | Commande clé | Résultat attendu |
|---|---|---|
| Serveur up | `curl /health` | `200 {"status":"ok"}` |
| Inscription | `POST /auth/register` | `201` + user |
| Inscription doublon | même email | `400`/`409` |
| Connexion | `POST /auth/login` (form-urlencoded) | `200` + token |
| Connexion échec | mauvais mdp | `401` |
| Chat | `POST /chat` + Bearer token | `200` + réponse IA |
| Chat sans token | idem sans header | `401` |
| Progress | `GET /progress/...` + token | `200` + stats |
| Speech (STT) | `POST /speech/...` + fichier audio | `200` + texte transcrit |
| Speech (TTS) | `POST /speech/...` + texte | `200` + fichier audio |

---

## 8. Si quelque chose plante (500)

Ne devine pas — copie-colle-moi :
1. Le traceback complet affiché dans le terminal uvicorn (pas juste le message d'erreur côté client)
2. La commande curl exacte (ou capture Swagger) que tu as utilisée
3. Le contenu du fichier de la route concernée si tu peux (ex. `app/routers/chat.py`)

C'est ce qui m'a permis de diagnostiquer rapidement tous les problèmes précédents (Gemini, Postgres, table manquante, migrations).
