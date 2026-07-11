"""
Service Text-to-Speech.

Avant : basé sur les modèles TTS de Gemini (google-genai), qui
renvoyaient du PCM brut réencapsulé manuellement en WAV. Gemini a été
entièrement retiré du projet, donc la synthèse vocale tourne maintenant
via `edge-tts` : le moteur de synthèse vocale de Microsoft Edge, gratuit,
sans clé API, avec des voix françaises neurales de bonne qualité. Il
renvoie directement du MP3 (pas besoin de réencapsulation WAV manuelle).
"""
import logging
import os

import edge_tts

logger = logging.getLogger("app.tts")

# Voix française neutre par défaut ; liste des voix dispo via
# `edge-tts --list-voices | grep fr-FR`.
VOICE_NAME = os.getenv("TTS_VOICE", "fr-FR-DeniseNeural")


class SpeechSynthesisError(Exception):
    """Levée quand la synthèse vocale échoue."""


async def synthesize_speech(text: str) -> bytes:
    """Génère un fichier audio MP3 à partir d'un texte français."""
    if not text.strip():
        raise SpeechSynthesisError("Le texte à synthétiser est vide.")

    try:
        communicate = edge_tts.Communicate(text, VOICE_NAME)
        audio_chunks = bytearray()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.extend(chunk["data"])
    except Exception as exc:  # noqa: BLE001 - toute erreur réseau/lib devient une erreur métier
        logger.exception("Échec de la synthèse vocale")
        raise SpeechSynthesisError("Impossible de générer l'audio.") from exc

    if not audio_chunks:
        raise SpeechSynthesisError("Aucun audio généré par le moteur TTS.")

    return bytes(audio_chunks)
