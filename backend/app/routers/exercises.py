from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.config import settings
from app.core.deps import get_current_user
from app.core.redis_client import rate_limiter
from app.models.user import User
from app.models.exercise import Exercise
from app.models.progress import Progress
from app.schemas.exercise import ExerciseOut, ExerciseSubmitIn, ExerciseResultOut
from app.services import exercise_service
from app.services.llm_service import LLMServiceError

router = APIRouter(prefix="/exercises", tags=["exercises"])

# Réutilise le même bucket que /chat : la génération d'exercice appelle
# aussi le LLM, donc mérite la même protection anti-abus.
_exercise_rate_limit = rate_limiter("exercise-generate", settings.CHAT_RATE_LIMIT_PER_MINUTE)


@router.post(
    "/generate",
    response_model=ExerciseOut,
    dependencies=[Depends(_exercise_rate_limit)],
)
def generate_exercise(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Génère un exercice personnalisé (Phase 7), ciblé sur la catégorie
    d'erreur la plus fréquente de l'utilisateur si elle est connue.
    """
    progress = db.query(Progress).filter(Progress.user_id == current_user.id).first()
    try:
        exercise = exercise_service.generate_personalized_exercise(db, current_user, progress)
    except LLMServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc
    return exercise


@router.get("", response_model=list[ExerciseOut])
def list_my_exercises(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Historique des exercices de l'utilisateur connecté (les plus récents d'abord)."""
    return (
        db.query(Exercise)
        .filter(Exercise.user_id == current_user.id)
        .order_by(Exercise.created_at.desc())
        .all()
    )


@router.post("/{exercise_id}/submit", response_model=ExerciseResultOut)
def submit_exercise(
    exercise_id: int,
    payload: ExerciseSubmitIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soumet une réponse à un exercice et reçoit la correction immédiate."""
    exercise = (
        db.query(Exercise)
        .filter(Exercise.id == exercise_id, Exercise.user_id == current_user.id)
        .first()
    )
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercice introuvable.")

    return exercise_service.submit_exercise_answer(db, exercise, payload.reponse)
