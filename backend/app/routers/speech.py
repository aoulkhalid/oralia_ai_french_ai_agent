from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.redis_client import rate_limiter
from app.models.user import User
from app.schemas.chat import TranscriptionOut, TextToSpeechIn
from app.services import stt_service, tts_service
from app.services.stt_service import TranscriptionError
from app.services.tts_service import SpeechSynthesisError

router = APIRouter(prefix="/speech", tags=["speech"])

# Types MIME couramment produits par MediaRecorder côté navigateur.
# faster-whisper (via ffmpeg) sait décoder tous ces formats.
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

_stt_rate_limit = rate_limiter("speech-stt", settings.SPEECH_RATE_LIMIT_PER_MINUTE)
_tts_rate_limit = rate_limiter("speech-tts", settings.SPEECH_RATE_LIMIT_PER_MINUTE)


@router.post(
    "/speech-to-text",
    response_model=TranscriptionOut,
    dependencies=[Depends(_stt_rate_limit)],
)
async def speech_to_text(
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Transcrit un enregistrement audio (micro du frontend) en texte français."""
    mime_type = audio.content_type or "audio/webm"
    if mime_type not in _ALLOWED_AUDIO_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Type audio non supporté : {mime_type}.",
        )

    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Fichier audio vide.")

    try:
        text = stt_service.transcribe_audio(audio_bytes, mime_type=mime_type)
    except TranscriptionError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return TranscriptionOut(text=text)


@router.post("/text-to-speech", dependencies=[Depends(_tts_rate_limit)])
async def text_to_speech(
    payload: TextToSpeechIn,
    current_user: User = Depends(get_current_user),
):
    """Synthétise un texte français en audio (MP3)."""
    if not payload.text.strip():
        raise HTTPException(status_code=400, detail="Le texte à synthétiser est vide.")

    try:
        audio_bytes = await tts_service.synthesize_speech(payload.text)
    except SpeechSynthesisError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return Response(content=audio_bytes, media_type="audio/mpeg")
