"""
Service de persistance des conversations : création/récupération,
sauvegarde des messages et corrections, historique, mise à jour de
la progression de l'utilisateur.
"""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.correction import Correction
from app.models.progress import Progress
from app.models.user import User

# Nombre de derniers messages envoyés au LLM comme contexte de conversation
MAX_HISTORY_MESSAGES = 12


def get_or_create_conversation(
    db: Session, user: User, conversation_id: int | None
) -> Conversation:
    """Récupère une conversation existante (si elle appartient à l'utilisateur)
    ou en crée une nouvelle."""
    if conversation_id is not None:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user.id,
            )
            .first()
        )
        if conversation:
            return conversation

    conversation = Conversation(user_id=user.id, niveau_cecrl=user.niveau_cecrl)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_recent_history(
    db: Session, conversation: Conversation, limit: int = MAX_HISTORY_MESSAGES
) -> list[dict]:
    """Retourne les derniers messages de la conversation, du plus ancien au
    plus récent, au format attendu par llm_service.generate_reply."""
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )
    messages.reverse()
    return [{"role": m.role, "content": m.content} for m in messages]


def save_message(
    db: Session, conversation: Conversation, role: str, content: str
) -> Message:
    message = Message(conversation_id=conversation.id, role=role, content=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def save_corrections(
    db: Session, message: Message, correction_data: dict
) -> list[Correction]:
    """Enregistre les corrections détectées sur un message utilisateur."""
    corrections: list[Correction] = []
    for err in correction_data.get("erreurs", []):
        correction = Correction(
            message_id=message.id,
            erreur_originale=err.get("erreur_originale", ""),
            texte_corrige=err.get("texte_corrige", ""),
            explication=err.get("explication"),
            type_erreur=err.get("type_erreur"),
        )
        db.add(correction)
        corrections.append(correction)

    if corrections:
        db.commit()
        for c in corrections:
            db.refresh(c)
    return corrections


def update_progress(
    db: Session,
    user: User,
    nb_new_corrections: int,
    types_erreurs: list[str | None],
) -> Progress:
    """Met à jour le tableau de bord de progression après un échange."""
    progress = db.query(Progress).filter(Progress.user_id == user.id).first()
    if not progress:
        progress = Progress(user_id=user.id, niveau_actuel=user.niveau_cecrl)
        db.add(progress)

    progress.total_messages = (progress.total_messages or 0) + 1
    progress.total_corrections = (progress.total_corrections or 0) + nb_new_corrections

    frequences = {e["type"]: e["count"] for e in (progress.erreurs_frequentes or [])}
    for type_erreur in types_erreurs:
        if not type_erreur:
            continue
        frequences[type_erreur] = frequences.get(type_erreur, 0) + 1

    progress.erreurs_frequentes = sorted(
        [{"type": t, "count": c} for t, c in frequences.items()],
        key=lambda x: x["count"],
        reverse=True,
    )

    db.commit()
    db.refresh(progress)
    return progress


def close_conversation(db: Session, conversation: Conversation) -> Conversation:
    """Marque une conversation comme terminée et incrémente le compteur
    de conversations complétées dans la progression de l'utilisateur."""
    conversation.ended_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(conversation)

    progress = (
        db.query(Progress).filter(Progress.user_id == conversation.user_id).first()
    )
    if progress:
        progress.conversations_completees = (progress.conversations_completees or 0) + 1
        db.commit()

    return conversation