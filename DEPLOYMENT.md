# Guide de déploiement en production

Ce document couvre ce que le code peut vous fournir tout seul (Docker,
CI, migrations) et ce qui reste, par nature, une décision qui vous
appartient (hébergeur, nom de domaine, moyen de paiement) — je ne peux
pas créer de compte cloud ou de compte Stripe à votre place.

---

## 1. Ce qui est déjà prêt dans le projet

- `backend/Dockerfile`, `frontend/Dockerfile` : images de production.
- `docker-compose.prod.yml` : variante production de `docker-compose.yml`
  (pas de ports Postgres/Redis exposés à l'hôte, `restart: always`,
  logs JSON via `LOG_FORMAT=json`).
- `.github/workflows/ci.yml` : tests backend + build frontend + build des
  images Docker à chaque push/PR.
- Migrations Alembic appliquées automatiquement au démarrage du conteneur
  backend (`alembic upgrade head && uvicorn ...`, voir `backend/Dockerfile`).
- `/health` et `/health/full` : endpoints de santé pour la probe de votre
  hébergeur.

## 2. Ce qu'il vous reste à choisir

### Hébergeur

Trois options courantes, du plus simple au plus flexible :

**Railway ou Render** (le plus simple pour démarrer)
- Créez un service PostgreSQL et un service Redis managés directement
  depuis leur interface (pas besoin de les faire tourner vous-même).
- Créez un service "Docker" pointant sur `backend/Dockerfile`, avec les
  variables d'environnement de `backend/.env.example` renseignées dans
  leur interface (jamais commitées).
- Idem pour `frontend/Dockerfile`, avec `NEXT_PUBLIC_API_URL` pointant
  vers l'URL publique du service backend.
- Ces deux plateformes gèrent le TLS/HTTPS et le nom de domaine pour vous.

**Fly.io** (bon compromis simplicité/contrôle)
- `fly launch` détecte les Dockerfiles automatiquement.
- Nécessite `fly.toml` par service (non fourni ici, dépend de votre
  organisation en apps Fly).

**VPS (Hetzner, DigitalOcean, OVH...)** (contrôle total, plus de travail)
- Installez Docker + Docker Compose sur le serveur.
- Copiez le projet, `cp backend/.env.example backend/.env` et remplissez
  les vraies valeurs de production.
- `docker compose -f docker-compose.prod.yml --env-file .env.prod up -d --build`
- Ajoutez un reverse proxy pour le TLS : le moyen le plus simple est
  **Caddy** (bloc commenté dans `docker-compose.prod.yml`), qui gère les
  certificats Let's Encrypt automatiquement. Exemple de `Caddyfile` :
  ```
  mondomaine.com {
      reverse_proxy frontend:3000
  }
  api.mondomaine.com {
      reverse_proxy backend:8000
  }
  ```

### Nom de domaine

Achetez-le où vous voulez (Namecheap, OVH, Google Domains...), pointez un
enregistrement A vers l'IP de votre VPS, ou suivez les instructions DNS
spécifiques si vous utilisez Railway/Render/Fly (ils fournissent
généralement un sous-domaine gratuit par défaut, ex: `monapp.up.railway.app`).

### Secrets de production

Ne réutilisez JAMAIS les valeurs de `backend/.env` de développement en
production. Générez de nouvelles valeurs :
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"   # JWT_SECRET_KEY
```
Utilisez le gestionnaire de secrets de votre hébergeur (Railway/Render
ont un onglet "Variables" dédié) plutôt qu'un fichier `.env` sur le
serveur si possible.

### Paiement (freemium/premium)

`backend/app/routers/billing.py` contient un **scaffold**, pas une vraie
intégration de paiement (voir les commentaires en tête de ce fichier).
Pour facturer réellement :
1. Créez un compte [Stripe](https://stripe.com) (ou équivalent).
2. Remplacez `POST /billing/upgrade` par une redirection vers une session
   Stripe Checkout.
3. Ajoutez un endpoint webhook qui active `user.plan = "premium"`
   uniquement sur réception d'un événement Stripe confirmé — jamais
   depuis une requête directe du navigateur.

### Conformité RGPD complète

`GET /auth/me/data-export` et `DELETE /auth/me` fournissent les
mécanismes techniques (portabilité, effacement). Une conformité RGPD
complète implique aussi, en dehors du code :
- Une politique de confidentialité publiée sur le site.
- Un registre des traitements de données.
- Le choix d'une base légale pour chaque traitement (ex: exécution du
  contrat pour l'authentification, intérêt légitime pour les statistiques
  d'usage).
- Le cas échéant, la désignation d'un DPO (Délégué à la Protection des
  Données) si le volume/la nature des données l'exige.

---

## 3. Checklist avant mise en production

- [ ] Nouvelles valeurs pour `JWT_SECRET_KEY`, `LLM_API_KEY`, mots de
      passe PostgreSQL/Redis (jamais celles de dev)
- [ ] `CORS_ORIGINS` pointe vers le vrai domaine du frontend (pas
      `localhost`)
- [ ] `LOG_FORMAT=json` activé pour l'agrégation de logs
- [ ] TLS/HTTPS actif (géré par l'hébergeur ou Caddy/Nginx)
- [ ] Sauvegardes automatiques de PostgreSQL configurées côté hébergeur
- [ ] Alerting basique sur `/health/full` (ex: UptimeRobot, gratuit)
- [ ] Vérifié que `backend/.env` n'est jamais commité (déjà dans
      `.gitignore`)
