"""
Service responsable de la génération de réponses conversationnelles
et des corrections grammaticales via l'API Gemini (Google).

- generate_reply(message, niveau_cecrl, historique) -> str
- correct_message(message) -> dict
"""

import json
import os

from google import genai
from google.genai import types

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ---------------------------------------------------------------------------
# Adaptation au niveau CECRL
# ---------------------------------------------------------------------------

NIVEAU_INSTRUCTIONS = {
    "A1": (
        "Utilise des phrases très courtes et simples, au présent uniquement. "
        "Vocabulaire de base (famille, quotidien, nombres, salutations). "
        "Une seule idée par phrase. Reformule immédiatement si l'utilisateur "
        "ne semble pas comprendre."
    ),
    "A2": (
        "Utilise des phrases simples, passé composé et futur proche autorisés. "
        "Vocabulaire courant (achats, transports, loisirs). Évite les "
        "expressions idiomatiques."
    ),
    "B1": (
        "Phrases de complexité moyenne, tous les temps courants autorisés "
        "(imparfait, conditionnel simple). Tu peux introduire quelques "
        "expressions idiomatiques courantes en les expliquant si besoin."
    ),
    "B2": (
        "Discours naturel et nuancé, subjonctif autorisé. Vocabulaire varié, "
        "y compris abstrait. Tu peux débattre et nuancer ton propos."
    ),
    "C1": (
        "Registre soutenu possible, structures complexes, nuances fines, "
        "expressions idiomatiques et registre familier selon le contexte."
    ),
    "C2": (
        "Registre natif complet, aucune limitation de vocabulaire ni de "
        "structure. Tu peux jouer avec la langue (humour, ironie, registre "
        "littéraire)."
    ),
}


def build_system_prompt(niveau_cecrl: str) -> str:
    consigne_niveau = NIVEAU_INSTRUCTIONS.get(niveau_cecrl, NIVEAU_INSTRUCTIONS["A1"])
    return (
        "Tu es un partenaire de conversation en français, bienveillant et "
        "patient, pour un apprenant de niveau CECRL "
        f"{niveau_cecrl}.\n\n"
        f"Consigne de niveau : {consigne_niveau}\n\n"
        "Règles générales :\n"
        "- Réponds UNIQUEMENT en français.\n"
        "- Reste naturel et conversationnel, comme une vraie discussion, pas "
        "un cours magistral.\n"
        "- Pose une question de relance à la fin de ta réponse pour "
        "maintenir la conversation.\n"
        "- Ne corrige PAS les erreurs de l'utilisateur dans ta réponse "
        "(un autre service s'en charge séparément) : contente-toi de "
        "répondre naturellement au message.\n"
        "- Garde des réponses courtes (2 à 4 phrases maximum)."
    )


def _build_contents(message: str, historique: list[dict]) -> list[types.Content]:
    """Convertit l'historique (roles user/assistant) au format de contenus
    attendu par l'API Gemini (roles user/model)."""
    contents: list[types.Content] = []
    for h in historique:
        role = h.get("role")
        if role not in ("user", "assistant"):
            continue
        gemini_role = "model" if role == "assistant" else "user"
        contents.append(
            types.Content(
                role=gemini_role,
                parts=[types.Part.from_text(text=h.get("content", ""))],
            )
        )
    contents.append(
        types.Content(role="user", parts=[types.Part.from_text(text=message)])
    )
    return contents


def generate_reply(
    message: str,
    niveau_cecrl: str = "A1",
    historique: list[dict] | None = None,
) -> str:
    """
    Génère la réponse conversationnelle de l'agent.

    - message : dernier message de l'utilisateur
    - niveau_cecrl : niveau CECRL courant de l'utilisateur (A1..C2)
    - historique : liste de dicts [{"role": "user"|"assistant", "content": str}, ...]
                    (contexte de la conversation, du plus ancien au plus récent)
    """
    historique = historique or []

    response = _client.models.generate_content(
        model=MODEL,
        contents=_build_contents(message, historique),
        config=types.GenerateContentConfig(
            system_instruction=build_system_prompt(niveau_cecrl),
            temperature=0.7,
            max_output_tokens=300,
        ),
    )
    return (response.text or "").strip()


# ---------------------------------------------------------------------------
# Correction grammaticale
# ---------------------------------------------------------------------------

CORRECTION_SYSTEM_PROMPT = """Tu es un correcteur de français expert.

Analyse le message de l'utilisateur et identifie les erreurs de grammaire,
conjugaison, orthographe, accord ou vocabulaire.

Réponds STRICTEMENT en JSON avec ce format, sans texte autour :
{
  "has_errors": true|false,
  "erreurs": [
    {
      "erreur": "extrait fautif exact",
      "correction": "version corrigée de cet extrait",
      "explication": "explication courte et pédagogique en français",
      "categorie": "grammaire" | "conjugaison" | "orthographe" | "accord" | "vocabulaire"
    }
  ]
}

Si le message est correct, renvoie has_errors: false et erreurs: [].
Ne signale jamais une erreur pour une formulation familière mais correcte.
"""


def correct_message(message: str) -> dict:
    """
    Analyse un message utilisateur et renvoie les erreurs détectées.

    Retourne un dict :
    {
        "has_errors": bool,
        "erreurs": [
            {
                "erreur": str,
                "correction": str,
                "explication": str,
                "categorie": str,
            },
            ...
        ],
    }
    """
    response = _client.models.generate_content(
        model=MODEL,
        contents=message,
        config=types.GenerateContentConfig(
            system_instruction=CORRECTION_SYSTEM_PROMPT,
            temperature=0,
            response_mime_type="application/json",
        ),
    )

    raw = response.text
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        data = {"has_errors": False, "erreurs": []}

    data.setdefault("erreurs", [])
    data.setdefault("has_errors", bool(data["erreurs"]))
    return data
