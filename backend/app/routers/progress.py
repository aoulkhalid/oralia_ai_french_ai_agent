import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.progress import Progress
from app.services import conversation_service

router = APIRouter(prefix="/progress", tags=["progress"])


def _load_erreurs_frequentes(progress: Progress) -> list[dict]:
    try:
        return json.loads(progress.erreurs_frequentes) if progress.erreurs_frequentes else []
    except (json.JSONDecodeError, TypeError):
        return []


def _check_access(user_id: int, current_user: User) -> None:
    # Un utilisateur ne peut consulter que son propre tableau de bord
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez consulter que votre propre progression.",
        )


@router.get("/{user_id}")
def get_progress(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _check_access(user_id, current_user)

    progress = db.query(Progress).filter(Progress.user_id == user_id).first()
    if not progress:
        raise HTTPException(status_code=404, detail="Progression introuvable.")

    return {
        "user_id": user_id,
        "niveau_estime": progress.niveau_estime,
        "conversations_completees": progress.conversations_completees,
        "erreurs_frequentes": _load_erreurs_frequentes(progress),
    }


@router.get("/{user_id}/dashboard")
def get_progress_dashboard(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Tableau de bord de progression complet (Phase 6) : niveau CECRL actuel,
    conversations complétées, répartition des erreurs par catégorie,
    historique des changements de niveau et tendance des corrections par
    semaine — tout ce qu'il faut pour les graphiques du frontend.
    """
    _check_access(user_id, current_user)

    progress = db.query(Progress).filter(Progress.user_id == user_id).first()
    if not progress:
        # Pas encore de conversation : dashboard vide mais valide, plutôt
        # qu'une 404 qui obligerait le frontend à gérer un cas d'erreur
        # pour un utilisateur simplement tout neuf.
        return {
            "user_id": user_id,
            "niveau_estime": current_user.niveau_cecrl,
            "conversations_completees": 0,
            "erreurs_frequentes": [],
            "niveau_historique": [],
            "erreurs_par_semaine": [],
            "points": 0,
            "streak_jours": 0,
            "badges": [],
        }

    stats = conversation_service.get_progression_stats(db, user_id)

    return {
        "user_id": user_id,
        "niveau_estime": progress.niveau_estime,
        "conversations_completees": progress.conversations_completees,
        "erreurs_frequentes": _load_erreurs_frequentes(progress),
        "points": progress.points,
        "streak_jours": progress.streak_jours,
        "badges": conversation_service.compute_badges(progress),
        **stats,
    }
