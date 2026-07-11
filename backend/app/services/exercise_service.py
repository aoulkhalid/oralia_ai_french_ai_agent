"""
Génération d'exercices personnalisés (Phase 7).

Principe : on regarde les catégories d'erreurs les plus fréquentes de
l'utilisateur (déjà calculées dans Progress.erreurs_frequentes par
conversation_service.update_progress), et on demande au LLM de générer un
exercice ciblé sur sa catégorie d'erreur n°1 — un exercice générique
"au hasard" aurait beaucoup moins de valeur pédagogique.
"""
import json
import logging

from sqlalchemy.orm import Session

from app.models.exercise import Exercise
from app.models.progress import Progress
from app.models.user import User
from app.services.llm_service import _create_completion, LLMServiceError
from app.core.config import settings

logger = logging.getLogger("app.exercises")

EXERCISE_SYSTEM_PROMPT = """Tu es un professeur de français qui crée des exercices ciblés.

Génère UN exercice à trous ou de correction, adapté au niveau CECRL et à
la catégorie d'erreur donnés. Réponds STRICTEMENT en JSON, sans texte
autour :
{
  "question": "l'énoncé de l'exercice, en français, avec un trou marqué par ___ si pertinent",
  "reponse_attendue": "la réponse correcte exacte attendue"
}

L'exercice doit être résoluble avec une réponse courte (un mot, une
expression, ou une phrase corrigée), pas une réponse ouverte/longue.
"""


def _default_categorie(progress: Progress | None) -> str | None:
    """Détermine la catégorie d'erreur n°1 de l'utilisateur, si connue."""
    if not progress or not progress.erreurs_frequentes:
        return None
    try:
        erreurs = json.loads(progress.erreurs_frequentes)
        if erreurs:
            return erreurs[0].get("categorie")
    except (json.JSONDecodeError, TypeError, IndexError, KeyError):
        pass
    return None


def generate_personalized_exercise(
    db: Session, user: User, progress: Progress | None
) -> Exercise:
    """
    Génère et sauvegarde un exercice ciblé sur la catégorie d'erreur la
    plus fréquente de l'utilisateur (ou un exercice général de son niveau
    s'il n'a pas encore assez d'historique de corrections).
    """
    categorie = _default_categorie(progress)
    niveau = user.niveau_cecrl or "A1"

    consigne = (
        f"Niveau CECRL : {niveau}. "
        + (
            f"Catégorie d'erreur à cibler en priorité : {categorie}."
            if categorie
            else "Aucune catégorie d'erreur spécifique connue : génère un "
            "exercice général adapté à ce niveau."
        )
    )

    try:
        response = _create_completion(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": EXERCISE_SYSTEM_PROMPT},
                {"role": "user", "content": consigne},
            ],
            temperature=0.8,
            response_format={"type": "json_object"},
        )
        data = json.loads(response.choices[0].message.content)
        question = data["question"]
        reponse_attendue = data["reponse_attendue"]
    except LLMServiceError:
        raise
    except Exception as exc:  # noqa: BLE001 - réponse LLM malformée, JSON invalide, etc.
        logger.error("Échec de la génération d'exercice : %s", exc)
        raise LLMServiceError("Impossible de générer un exercice pour le moment.") from exc

    exercise = Exercise(
        user_id=user.id,
        niveau_cecrl=niveau,
        categorie=categorie,
        question=question,
        reponse_attendue=reponse_attendue,
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)
    return exercise


def _normalize(text: str) -> str:
    return " ".join(text.strip().lower().split())


def submit_exercise_answer(db: Session, exercise: Exercise, reponse: str) -> dict:
    """
    Corrige la réponse de l'utilisateur. Comparaison normalisée (espaces,
    casse) plutôt qu'un LLM ici : ces exercices ont une réponse fermée et
    courte, une comparaison textuelle est plus fiable et instantanée
    qu'un jugement LLM pour ce cas précis.
    """
    is_correct = _normalize(reponse) == _normalize(exercise.reponse_attendue)

    exercise.reponse_utilisateur = reponse
    exercise.is_correct = is_correct
    db.commit()
    db.refresh(exercise)

    feedback = (
        "Bravo, c'est correct !"
        if is_correct
        else f"Ce n'est pas tout à fait ça. La réponse attendue était : « {exercise.reponse_attendue} »."
    )

    return {
        "id": exercise.id,
        "is_correct": is_correct,
        "reponse_attendue": exercise.reponse_attendue,
        "feedback": feedback,
    }
