from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatMessage(BaseModel):
    user_id: int
    message: str


class ChatResponse(BaseModel):
    reply: str
    correction: str | None = None


@router.post("", response_model=ChatResponse)
def send_message(payload: ChatMessage):
    # TODO: brancher ici le service LLM (app/services/llm_service.py)
    # pour générer la réponse + la correction grammaticale
    return ChatResponse(
        reply=f"(placeholder) Vous avez dit : {payload.message}",
        correction=None,
    )
