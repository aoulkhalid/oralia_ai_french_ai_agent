from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.redis_client import check_redis_connection

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    """Liveness check basique (l'API répond)."""
    return {"status": "ok"}


@router.get("/health/full")
async def health_check_full(db: Session = Depends(get_db)):
    """Readiness check : vérifie aussi la base de données et Redis, utile
    pour les orchestrateurs (Docker healthcheck, Kubernetes readinessProbe)."""
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_ok = False

    redis_ok = await check_redis_connection()

    status_ok = db_ok and redis_ok
    return {
        "status": "ok" if status_ok else "degraded",
        "database": "ok" if db_ok else "unreachable",
        "redis": "ok" if redis_ok else "unreachable",
    }
