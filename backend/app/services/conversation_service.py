"""
Service de persistance des conversations : création/récupération,
sauvegarde des messages et corrections, historique, mise à jour de
la progression de l'utilisateur.
"""

import json
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

    # NB : Conversation n'a plus de colonne niveau_cecrl (le niveau est
    # toujours lu depuis l'utilisateur, cf. llm_service.generate_reply).
    conversation = Conversation(user_id=user.id)
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
    return [{"role": m.role, "content": m.contenu} for m in messages]


def save_message(
    db: Session, conversation: Conversation, role: str, content: str
) -> Message:
    message = Message(conversation_id=conversation.id, role=role, contenu=content)
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
            erreur=err.get("erreur", ""),
            correction=err.get("correction", ""),
            explication=err.get("explication"),
            categorie=err.get("categorie"),
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
    categories_erreurs: list[str | None],
) -> Progress:
    """Met à jour le tableau de bord de progression après un échange.

    NB : `erreurs_frequentes` est une colonne String (JSON sérialisé en
    texte), pas une colonne JSON native : on doit donc json.loads/json.dumps
    nous-mêmes.
    """
    progress = db.query(Progress).filter(Progress.user_id == user.id).first()
    if not progress:
        progress = Progress(user_id=user.id, niveau_estime=user.niveau_cecrl)
        db.add(progress)
        db.commit()
        db.refresh(progress)

    frequences: dict[str, int] = {}
    if progress.erreurs_frequentes:
        try:
            existing = json.loads(progress.erreurs_frequentes)
            frequences = {e["categorie"]: e["count"] for e in existing}
        except (json.JSONDecodeError, TypeError, KeyError):
            frequences = {}

    for categorie in categories_erreurs:
        if not categorie:
            continue
        frequences[categorie] = frequences.get(categorie, 0) + 1

    progress.erreurs_frequentes = json.dumps(
        sorted(
            [{"categorie": c, "count": n} for c, n in frequences.items()],
            key=lambda x: x["count"],
            reverse=True,
        )
    )
    progress.niveau_estime = progress.niveau_estime or user.niveau_cecrl

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
