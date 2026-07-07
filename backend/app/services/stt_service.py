"""
Service Speech-to-Text, basé sur la compréhension audio native de Gemini
(plus besoin d'un modèle Whisper séparé : Gemini accepte l'audio directement
en entrée de generate_content).
"""

import os

from google import genai
from google.genai import types

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

TRANSCRIBE_PROMPT = (
    "Transcris fidèlement, en français, exactement ce qui est dit dans cet "
    "enregistrement audio. Réponds UNIQUEMENT avec le texte transcrit, sans "
    "aucun commentaire, préambule ou guillemets."
)


def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/webm") -> str:
    """
    Transcrit un enregistrement audio (bytes bruts + type MIME, ex.
    "audio/webm", "audio/wav", "audio/mp3", "audio/ogg") en texte français.
    """
    response = _client.models.generate_content(
        model=MODEL,
        contents=[
            TRANSCRIBE_PROMPT,
            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
        ],
    )
    return (response.text or "").strip()
