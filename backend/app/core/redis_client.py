"""
Client Redis partagé + rate limiter simple ("fixed window") basé sur Redis.

Avant : Redis était déclaré dans docker-compose.yml mais n'était utilisé
nulle part dans le code — un service qui tourne pour rien. Maintenant :
Redis protège les routes qui appellent l'API du LLM (/chat,
/speech/speech-to-text, /speech/text-to-speech) contre les abus, ce qui
limite les coûts d'API et les risques de déni de service.
"""
import logging

import redis as redis_sync
import redis.asyncio as redis
from fastapi import Depends, HTTPException, status

from app.core.config import settings
from app.core.deps import get_current_user
from app.models.user import User

logger = logging.getLogger("app.redis")

_redis_client: redis.Redis | None = None
_redis_client_sync: redis_sync.Redis | None = None


def get_redis() -> redis.Redis:
    """Retourne un client Redis asynchrone unique (lazy singleton)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )
    return _redis_client


def get_redis_sync() -> redis_sync.Redis:
    """
    Client Redis synchrone (lazy singleton), pour les usages appelés
    depuis du code non-async (ex: cache de corrections LLM dans
    llm_service.py, appelé depuis une route FastAPI sync exécutée dans un
    threadpool). Évite d'avoir à faire tourner un event loop asyncio dans
    un contexte déjà threadé.
    """
    global _redis_client_sync
    if _redis_client_sync is None:
        _redis_client_sync = redis_sync.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )
    return _redis_client_sync


async def check_redis_connection() -> bool:
    """Utilisé par /health pour vérifier que Redis répond."""
    try:
        client = get_redis()
        await client.ping()
        return True
    except Exception:  # noqa: BLE001 - on veut juste un booléen de santé
        logger.exception("Échec du ping Redis")
        return False


def rate_limiter(bucket: str, limit_per_minute: int):
    """
    Fabrique une dépendance FastAPI qui limite un utilisateur à
    `limit_per_minute` requêtes par minute pour le `bucket` donné
    (ex: "chat", "speech-stt"), via un compteur Redis avec expiration.

    Si Redis est indisponible, on choisit de laisser passer la requête
    (fail-open) plutôt que de rendre toute l'application inutilisable à
    cause d'une dépendance annexe — mais on logue l'incident.

    Les utilisateurs "premium" (Phase 8, scaffold freemium) bénéficient
    d'une limite doublée : ce n'est qu'un exemple de modulation par plan,
    à affiner selon le vrai modèle tarifaire choisi.
    """

    async def _dependency(current_user: User = Depends(get_current_user)) -> None:
        key = f"ratelimit:{bucket}:{current_user.id}"
        effective_limit = (
            limit_per_minute * 2 if getattr(current_user, "plan", "free") == "premium" else limit_per_minute
        )
        try:
            client = get_redis()
            current = await client.incr(key)
            if current == 1:
                await client.expire(key, 60)
        except Exception:  # noqa: BLE001
            logger.exception("Redis indisponible pour le rate limiting (%s)", bucket)
            return

        if current > effective_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Trop de requêtes ({bucket}). "
                    f"Limite : {effective_limit} par minute."
                ),
            )

    return _dependency


def rate_limiter_by_ip(bucket: str, limit_per_minute: int):
    """
    Variante de rate_limiter pour les routes NON authentifiées (login,
    register) : la clé est l'adresse IP du client plutôt que l'ID
    utilisateur, puisqu'on n'a justement pas encore d'utilisateur
    authentifié à ce stade. Protège contre le brute-force de mots de
    passe et le spam de créations de compte.
    """
    from fastapi import Request

    async def _dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{bucket}:ip:{client_ip}"
        try:
            client = get_redis()
            current = await client.incr(key)
            if current == 1:
                await client.expire(key, 60)
        except Exception:  # noqa: BLE001
            logger.exception("Redis indisponible pour le rate limiting IP (%s)", bucket)
            return

        if current > limit_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Trop de tentatives. Réessayez dans une minute.",
            )

    return _dependency
