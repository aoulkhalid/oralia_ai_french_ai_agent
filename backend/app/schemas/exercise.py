from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ExerciseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    niveau_cecrl: str
    categorie: str | None = None
    question: str
    # Volontairement absent : reponse_attendue n'est jamais renvoyée avant
    # correction, sinon l'exercice n'a plus aucun intérêt pédagogique.
    reponse_utilisateur: str | None = None
    is_correct: bool | None = None
    created_at: datetime | None = None


class ExerciseSubmitIn(BaseModel):
    """Payload pour POST /exercises/{id}/submit."""

    reponse: str


class ExerciseResultOut(BaseModel):
    """Réponse après correction d'un exercice : révèle enfin la bonne réponse."""

    id: int
    is_correct: bool
    reponse_attendue: str
    feedback: str
