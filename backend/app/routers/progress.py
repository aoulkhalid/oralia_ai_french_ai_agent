from fastapi import APIRouter

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/{user_id}")
def get_progress(user_id: int):
    # TODO: récupérer les statistiques réelles depuis la base de données
    return {
        "user_id": user_id,
        "niveau_actuel": "B1",
        "conversations_completees": 0,
        "erreurs_frequentes": [],
    }
