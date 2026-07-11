"""
Service Speech-to-Text.

Avant : basé sur la compréhension audio native de Gemini
(google-genai). Gemini a été entièrement retiré du projet (le LLM ne
traite pas l'audio), donc la transcription tourne maintenant en local
avec faster-whisper (CTranslate2 + Whisper), sans clé API externe :
- Aucun appel réseau à un tiers pour transcrire l'audio (confidentialité).
- Aucun coût par appel.
- Le modèle est téléchargé une seule fois (mis en cache localement) lors
  de la première utilisation, puis réutilisé.

La taille du modèle Whisper (STT_MODEL_SIZE) est configurable : "tiny" ou
"base" pour un serveur peu puissant / CPU (rapide mais moins précis,
surtout avec un accent non natif), "small" (bon compromis précision/vitesse
sur CPU, recommandé par défaut ici), "medium"/"large-v3" pour la meilleure
précision si un GPU est disponible.
"""
import io
import logging
import os
import tempfile

from faster_whisper import WhisperModel

logger = logging.getLogger("app.stt")

# "small" par défaut : "base" confond trop de mots avec un accent non natif
# ou du bruit de fond. "small" reste utilisable sur CPU (quelques secondes
# par phrase) tout en étant nettement plus précis. Ajustable via .env.
_MODEL_SIZE = os.getenv("STT_MODEL_SIZE", "small")
_DEVICE = os.getenv("STT_DEVICE", "cpu")
_COMPUTE_TYPE = os.getenv("STT_COMPUTE_TYPE", "int8")  # int8 = rapide sur CPU

_model: WhisperModel | None = None


def _get_model() -> WhisperModel:
    """Charge le modèle Whisper une seule fois (lazy singleton) : le
    chargement prend plusieurs secondes, on ne veut pas le refaire à
    chaque requête."""
    global _model
    if _model is None:
        logger.info("Chargement du modèle Whisper '%s' (device=%s)", _MODEL_SIZE, _DEVICE)
        _model = WhisperModel(_MODEL_SIZE, device=_DEVICE, compute_type=_COMPUTE_TYPE)
    return _model


class TranscriptionError(Exception):
    """Levée quand la transcription échoue (audio corrompu, format non supporté, etc.)."""


def transcribe_audio(audio_bytes: bytes, mime_type: str = "audio/webm") -> str:
    """
    Transcrit un enregistrement audio (bytes bruts) en texte français.

    faster-whisper lit depuis un chemin de fichier ou un flux ; on passe
    par un fichier temporaire pour rester compatible avec tous les formats
    (webm, wav, mp3, ogg...) via le décodage ffmpeg interne de la lib.
    """
    if not audio_bytes:
        raise TranscriptionError("Fichier audio vide.")

    suffix = _suffix_from_mime(mime_type)
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
            tmp.write(audio_bytes)
            tmp.flush()

            model = _get_model()
            segments, _info = model.transcribe(
                tmp.name,
                language="fr",
                vad_filter=True,
                # min_silence_duration_ms plus élevé que le défaut (500ms) :
                # évite que le VAD coupe la transcription au milieu d'une
                # phrase pendant une courte hésitation.
                vad_parameters={"min_silence_duration_ms": 700},
                beam_size=10,
                best_of=5,
                # Évite que Whisper "s'auto-influence" d'un segment à
                # l'autre et parte dans des répétitions/hallucinations sur
                # de courts enregistrements (bug connu sur les modèles Whisper).
                condition_on_previous_text=False,
                # Indice de contexte : aide le modèle à mieux choisir entre
                # mots proches phonétiquement dans le domaine de
                # l'apprentissage du français (moins utile pour du
                # vocabulaire totalement hors-sujet).
                initial_prompt=(
                    "Conversation en français avec un apprenant de la langue, "
                    "sur des sujets du quotidien."
                ),
                # Descend un peu le seuil "pas de parole détectée" : évite
                # de couper le tout début ou la toute fin d'une phrase.
                no_speech_threshold=0.5,
            )
            text = " ".join(segment.text.strip() for segment in segments).strip()
    except Exception as exc:  # noqa: BLE001 - on convertit toute erreur bas niveau en erreur métier
        logger.exception("Échec de la transcription audio")
        raise TranscriptionError("Impossible de transcrire l'audio fourni.") from exc

    return text


def _suffix_from_mime(mime_type: str) -> str:
    return {
        "audio/webm": ".webm",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/mp3": ".mp3",
        "audio/mpeg": ".mp3",
        "audio/ogg": ".ogg",
        "audio/aac": ".aac",
        "audio/flac": ".flac",
    }.get(mime_type, ".webm")
