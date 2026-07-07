import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.progress import Progress

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/{user_id}")
def get_progress(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Un utilisateur ne peut consulter que son propre tableau de bord
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez consulter que votre propre progression.",
        )

    progress = db.query(Progress).filter(Progress.user_id == user_id).first()
    if not progress:
        raise HTTPException(status_code=404, detail="Progression introuvable.")

    try:
        erreurs_frequentes = (
            json.loads(progress.erreurs_frequentes) if progress.erreurs_frequentes else []
        )
    except (json.JSONDecodeError, TypeError):
        erreurs_frequentes = []

    return {
        "user_id": user_id,
        "niveau_estime": progress.niveau_estime,
        "conversations_completees": progress.conversations_completees,
        "erreurs_frequentes": erreurs_frequentes,
    }
