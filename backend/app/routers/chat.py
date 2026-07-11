from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.config import settings
from app.core.deps import get_current_user
from app.core.redis_client import rate_limiter
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import (
    ChatMessageIn,
    ChatResponse,
    MessageOut,
    ConversationOut,
)
from app.services import llm_service, conversation_service
from app.services.llm_service import LLMServiceError

router = APIRouter(prefix="/chat", tags=["chat"])

_chat_rate_limit = rate_limiter("chat", settings.CHAT_RATE_LIMIT_PER_MINUTE)


@router.post("", response_model=ChatResponse, dependencies=[Depends(_chat_rate_limit)])
def send_message(
    payload: ChatMessageIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Envoie un message à l'agent, sauvegarde l'échange et les corrections,
    et met à jour la progression de l'utilisateur.
    """
    conversation = conversation_service.get_or_create_conversation(
        db, current_user, payload.conversation_id, scenario_id=payload.scenario_id
    )

    # Contexte de conversation (derniers messages) pour le LLM
    historique = conversation_service.get_recent_history(db, conversation)
    scenario_context = conversation_service.get_scenario_context(db, conversation)

    # Génération de la réponse + correction, adaptées au niveau CECRL de l'utilisateur
    try:
        reply = llm_service.generate_reply(
            message=payload.message,
            niveau_cecrl=current_user.niveau_cecrl,
            historique=historique,
            scenario_context=scenario_context,
        )
    except LLMServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)
        ) from exc

    # La correction grammaticale est fail-safe (renvoie toujours un dict
    # valide même en cas d'échec du LLM) : elle ne doit jamais faire
    # échouer l'ensemble de l'échange de chat.
    correction_data = llm_service.correct_message(payload.message)

    # Persistance : message utilisateur, réponse de l'agent, corrections
    user_message = conversation_service.save_message(
        db, conversation, "user", payload.message
    )
    conversation_service.save_message(db, conversation, "assistant", reply)
    corrections = conversation_service.save_corrections(
        db, user_message, correction_data
    )

    conversation_service.update_progress(
        db,
        current_user,
        nb_new_corrections=len(corrections),
        categories_erreurs=[c.categorie for c in corrections],
    )

    return ChatResponse(
        conversation_id=conversation.id,
        reply=reply,
        corrections=corrections,
    )


@router.get("/conversations", response_model=list[ConversationOut])
def list_conversations(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Liste les conversations de l'utilisateur connecté."""
    return (
        db.query(Conversation)
        .filter(Conversation.user_id == current_user.id)
        .order_by(Conversation.created_at.desc())
        .all()
    )


@router.get("/{conversation_id}/history", response_model=list[MessageOut])
def get_conversation_history(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retourne l'historique complet d'une conversation de l'utilisateur."""
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation introuvable.")

    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.asc())
        .all()
    )


@router.post("/{conversation_id}/close", response_model=ConversationOut)
def close_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Clôture une conversation et incrémente les conversations complétées."""
    conversation = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id,
        )
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation introuvable.")

    return conversation_service.close_conversation(db, conversation)
