from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatMessageIn(BaseModel):
    """Payload pour POST /chat."""

    message: str
    conversation_id: int | None = None  # None = démarre une nouvelle conversation
    # Phase 7 : démarre la conversation dans le contexte d'un scénario
    # (ex: "Au restaurant", "Entretien d'embauche"). Ignoré si
    # conversation_id est fourni (le scénario est déjà fixé à la création).
    scenario_id: int | None = None


class CorrectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    # Alignés avec les colonnes réelles du modèle Correction
    # (erreur / correction / categorie), pas les anciens noms
    # erreur_originale / texte_corrige / type_erreur.
    erreur: str
    correction: str
    explication: str | None = None
    categorie: str | None = None


class ChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    conversation_id: int
    reply: str
    corrections: list[CorrectionOut] = []


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    contenu: str
    created_at: datetime
    corrections: list[CorrectionOut] = []


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titre: str | None = None
    scenario_id: int | None = None
    created_at: datetime
    ended_at: datetime | None = None


class TranscriptionOut(BaseModel):
    """Réponse de POST /speech/speech-to-text."""

    text: str


class TextToSpeechIn(BaseModel):
    """Payload pour POST /speech/text-to-speech."""

    text: str
