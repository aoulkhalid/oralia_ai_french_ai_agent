from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response

from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.chat import TranscriptionOut, TextToSpeechIn
from app.services import stt_service, tts_service

router = APIRouter(prefix="/speech", tags=["speech"])

# Types MIME acceptés par Gemini pour l'audio en entrée
_ALLOWED_AUDIO_TYPES = {
    "audio/webm",
    "audio/wav",
    "audio/x-wav",
    "audio/mp3",
    "audio/mpeg",
    "audio/ogg",
    "audio/aac",
    "audio/flac",
}


@router.post("/speech-to-text", response_model=TranscriptionOut)
async def speech_to_text(
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Transcrit un enregistrement audio (micro du frontend) en texte français."""
    mime_type = audio.content_type or "audio/webm"
    if mime_type not in _ALLOWED_AUDIO_TYPES:
        # On tente quand même avec le type déclaré : Gemini gère de
        # nombreux formats, on ne bloque donc pas trop agressivement.
        pass

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Fichier audio vide.")

    text = stt_service.transcribe_audio(audio_bytes, mime_type=mime_type)
    return TranscriptionOut(text=text)


@router.post("/text-to-speech")
def text_to_speech(
    payload: TextToSpeechIn,
    current_user: User = Depends(get_current_user),
):
    """Synthétise un texte français en audio (WAV) via Gemini TTS."""
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Le texte à synthétiser est vide.")

    audio_bytes = tts_service.synthesize_speech(payload.text)
    return Response(content=audio_bytes, media_type="audio/wav")
