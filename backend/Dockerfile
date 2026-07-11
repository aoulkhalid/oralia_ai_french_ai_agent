FROM python:3.12-slim

WORKDIR /app

# ffmpeg : requis par faster-whisper pour décoder webm/ogg/mp3/aac en entrée.
# libpq-dev + gcc : requis pour compiler psycopg2 (si la roue binaire
# psycopg2-binary n'est pas disponible pour l'archi cible).
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# Applique les migrations Alembic puis démarre l'API. En cas d'échec de
# connexion DB au tout premier démarrage (Postgres pas encore prêt),
# docker-compose relance le conteneur grâce à `restart: on-failure`.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
