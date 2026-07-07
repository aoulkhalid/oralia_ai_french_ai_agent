"""
Service Text-to-Speech, basé sur les modèles TTS de Gemini.

Gemini renvoie de l'audio PCM brut (16 bits, mono, 24 kHz) : on l'enveloppe
dans un conteneur WAV pour qu'il soit directement lisible par un <audio> côté
frontend, sans dépendance supplémentaire (ffmpeg, pydub, ...).
"""

import os
import struct

from google import genai
from google.genai import types

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
TTS_MODEL = os.getenv("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")
VOICE_NAME = os.getenv("GEMINI_TTS_VOICE", "Kore")

# Débit de l'audio renvoyé par les modèles TTS Gemini au 05/07/2026.
PCM_SAMPLE_RATE = 24000
PCM_CHANNELS = 1
PCM_SAMPLE_WIDTH = 2  # 16 bits


def _pcm_to_wav(pcm_data: bytes) -> bytes:
    """Enveloppe des données PCM brutes dans un conteneur WAV (en-tête RIFF)."""
    byte_rate = PCM_SAMPLE_RATE * PCM_CHANNELS * PCM_SAMPLE_WIDTH
    block_align = PCM_CHANNELS * PCM_SAMPLE_WIDTH
    data_size = len(pcm_data)

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        36 + data_size,
        b"WAVE",
        b"fmt ",
        16,  # taille du sous-bloc fmt
        1,  # PCM linéaire
        PCM_CHANNELS,
        PCM_SAMPLE_RATE,
        byte_rate,
        block_align,
        PCM_SAMPLE_WIDTH * 8,
        b"data",
        data_size,
    )
    return header + pcm_data


def synthesize_speech(text: str) -> bytes:
    """Génère un fichier audio WAV à partir d'un texte français."""
    response = _client.models.generate_content(
        model=TTS_MODEL,
        contents=f"Dis ceci d'une voix claire et naturelle, en français : {text}",
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=VOICE_NAME
                    )
                )
            ),
        ),
    )

    part = response.candidates[0].content.parts[0]
    pcm_data = part.inline_data.data
    return _pcm_to_wav(pcm_data)
