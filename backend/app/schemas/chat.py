from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatMessageIn(BaseModel):
    """Payload pour POST /chat."""

    message: str
    conversation_id: int | None = None  # None = démarre une nouvelle conversation


class CorrectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    erreur_originale: str
    texte_corrige: str
    explication: str | None = None
    type_erreur: str | None = None


class ChatResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    conversation_id: int
    reply: str
    corrections: list[CorrectionOut] = []


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    created_at: datetime
    corrections: list[CorrectionOut] = []


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titre: str | None = None
    niveau_cecrl: str
    started_at: datetime
    ended_at: datetime | None = None