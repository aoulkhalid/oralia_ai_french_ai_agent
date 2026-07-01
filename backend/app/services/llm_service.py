"""
Service responsable de la génération de réponses conversationnelles
et des corrections grammaticales via un LLM (OpenAI).

- generate_reply(message, niveau_cecrl, historique) -> str
- correct_message(message) -> dict
"""

import json
import os

from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

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


def _build_messages(
    message: str, niveau_cecrl: str, historique: list[dict]
) -> list[dict]:
    messages = [{"role": "system", "content": build_system_prompt(niveau_cecrl)}]
    for h in historique:
        role = h.get("role")
        if role not in ("user", "assistant"):
            continue
        messages.append({"role": role, "content": h.get("content", "")})
    messages.append({"role": "user", "content": message})
    return messages


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
    messages = _build_messages(message, niveau_cecrl, historique)

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()


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
      "erreur_originale": "extrait fautif exact",
      "texte_corrige": "version corrigée de cet extrait",
      "explication": "explication courte et pédagogique en français",
      "type_erreur": "grammaire" | "conjugaison" | "orthographe" | "accord" | "vocabulaire"
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
                "erreur_originale": str,
                "texte_corrige": str,
                "explication": str,
                "type_erreur": str,
            },
            ...
        ],
    }
    """
    messages = [
        {"role": "system", "content": CORRECTION_SYSTEM_PROMPT},
        {"role": "user", "content": message},
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        data = {"has_errors": False, "erreurs": []}

    data.setdefault("erreurs", [])
    data.setdefault("has_errors", bool(data["erreurs"]))
    return data