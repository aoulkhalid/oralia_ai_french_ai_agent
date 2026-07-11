"""
Service unique responsable de tous les appels au modèle de langage
(génération conversationnelle + correction grammaticale).

Le fournisseur n'est PAS codé en dur : n'importe quelle API compatible
OpenAI fonctionne (Groq, DeepSeek, Ollama en local, etc.), en changeant
uniquement LLM_BASE_URL / LLM_MODEL / LLM_API_KEY dans backend/.env — le
code ci-dessous ne change jamais. Configuré par défaut sur Groq (gratuit).

Fournit :
- generate_reply(message, niveau_cecrl, historique) -> str
- correct_message(message) -> dict

Gestion des erreurs : chaque appel réseau est protégé par un timeout
explicite et une politique de retry avec backoff exponentiel (tenacity),
qui ne réessaie que sur les erreurs transitoires (timeout, connexion,
erreurs serveur 5xx / rate limit 429) — jamais sur une erreur
d'authentification (401) ou de payload invalide (400), qui échoueraient
de la même façon à chaque tentative.
"""
import hashlib
import json
import logging

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
    RateLimitError,
)
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.core.redis_client import get_redis_sync

logger = logging.getLogger("app.llm")

_client = OpenAI(
    api_key=settings.LLM_API_KEY,
    base_url=settings.LLM_BASE_URL,
    timeout=settings.LLM_TIMEOUT_SECONDS,
)

_RETRYABLE_ERRORS = (APIConnectionError, APITimeoutError, RateLimitError)

_retry_policy = retry(
    reraise=True,
    stop=stop_after_attempt(settings.LLM_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(_RETRYABLE_ERRORS),
    before_sleep=lambda retry_state: logger.warning(
        "Appel LLM échoué (tentative %s/%s), nouvelle tentative dans %.1fs : %s",
        retry_state.attempt_number,
        settings.LLM_MAX_RETRIES,
        retry_state.next_action.sleep if retry_state.next_action else 0,
        retry_state.outcome.exception() if retry_state.outcome else "",
    ),
)


class LLMServiceError(Exception):
    """Erreur métier levée quand le LLM échoue après tous les retries."""


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


def build_system_prompt(niveau_cecrl: str, scenario_context: str | None = None) -> str:
    consigne_niveau = NIVEAU_INSTRUCTIONS.get(niveau_cecrl, NIVEAU_INSTRUCTIONS["A1"])
    scenario_bloc = (
        f"\n\nContexte de la conversation (scénario) : {scenario_context}\n"
        "Reste fidèle à ce rôle/contexte tout au long de l'échange."
        if scenario_context
        else ""
    )
    return (
        "Tu es un partenaire de conversation en français, bienveillant et "
        "patient, pour un apprenant de niveau CECRL "
        f"{niveau_cecrl}.\n\n"
        f"Consigne de niveau : {consigne_niveau}"
        f"{scenario_bloc}\n\n"
        "Règles générales :\n"
        "- Réponds UNIQUEMENT en français.\n"
        "- Reste naturel et conversationnel, comme une vraie discussion, pas "
        "un cours magistral.\n"
        "- Pose une question de relance à la fin de ta réponse pour "
        "maintenir la conversation.\n"
        "- Ne corrige PAS les erreurs de l'utilisateur dans ta réponse "
        "(un autre appel s'en charge séparément) : contente-toi de "
        "répondre naturellement au message.\n"
        "- Garde des réponses courtes (2 à 4 phrases maximum)."
    )


def _build_messages(
    message: str,
    niveau_cecrl: str,
    historique: list[dict],
    scenario_context: str | None = None,
) -> list[dict]:
    """Convertit l'historique (rôles user/assistant) au format de messages
    attendu par l'API compatible OpenAI (system, user, assistant)."""
    messages: list[dict] = [
        {"role": "system", "content": build_system_prompt(niveau_cecrl, scenario_context)}
    ]
    for h in historique:
        role = h.get("role")
        if role not in ("user", "assistant"):
            continue
        messages.append({"role": role, "content": h.get("content", "")})
    messages.append({"role": "user", "content": message})
    return messages


@_retry_policy
def _create_completion(**kwargs):
    """Appel bas niveau à l'API LLM, isolé pour être décoré par la
    politique de retry (permet de la réutiliser pour generate_reply ET
    correct_message sans dupliquer le décorateur)."""
    return _client.chat.completions.create(**kwargs)


def generate_reply(
    message: str,
    niveau_cecrl: str = "A1",
    historique: list[dict] | None = None,
    scenario_context: str | None = None,
) -> str:
    """
    Génère la réponse conversationnelle de l'agent.

    - message : dernier message de l'utilisateur
    - niveau_cecrl : niveau CECRL courant de l'utilisateur (A1..C2)
    - historique : liste de dicts [{"role": "user"|"assistant", "content": str}, ...]
                    (contexte de la conversation, du plus ancien au plus récent)
    - scenario_context : instructions de mise en situation (Phase 7),
                          ex: "Tu joues le rôle d'un serveur au restaurant..."

    Lève LLMServiceError si l'appel échoue définitivement (après retries).
    """
    historique = historique or []

    try:
        response = _create_completion(
            model=settings.LLM_MODEL,
            messages=_build_messages(message, niveau_cecrl, historique, scenario_context),
            temperature=0.7,
            max_tokens=300,
        )
    except APIStatusError as exc:
        logger.error("Le LLM a renvoyé une erreur HTTP %s : %s", exc.status_code, exc)
        raise LLMServiceError("Le service de conversation IA a renvoyé une erreur.") from exc
    except _RETRYABLE_ERRORS as exc:
        logger.error("LLM injoignable après %s tentatives : %s", settings.LLM_MAX_RETRIES, exc)
        raise LLMServiceError("Le service de conversation IA est temporairement indisponible.") from exc

    return (response.choices[0].message.content or "").strip()


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


CORRECTION_CACHE_TTL_SECONDS = 60 * 60 * 24 * 7  # 7 jours


def _correction_cache_key(message: str) -> str:
    # Les corrections ne dépendent que du texte exact du message (pas de
    # l'utilisateur ni du contexte) : un même message mal orthographié
    # produit toujours la même correction, donc une clé globale (pas par
    # utilisateur) maximise le taux de cache hit entre utilisateurs.
    digest = hashlib.sha256(message.strip().lower().encode("utf-8")).hexdigest()
    return f"llm:correction:{digest}"


def correct_message(message: str) -> dict:
    """
    Analyse un message utilisateur et renvoie les erreurs détectées.

    Retourne toujours un dict de la forme :
    {"has_errors": bool, "erreurs": [{"erreur", "correction", "explication", "categorie"}, ...]}
    même en cas d'échec du LLM ou de réponse JSON invalide (fail-safe : une
    correction manquante ne doit jamais faire planter tout le endpoint /chat).

    Optimisation coûts (Phase 8) : les résultats sont mis en cache dans
    Redis pendant CORRECTION_CACHE_TTL_SECONDS. Les mêmes fautes typiques
    ("je suis alle", "j'ai vu un chat noir dans la rue hier") reviennent
    très souvent chez différents apprenants ; éviter de repayer un appel
    LLM à chaque fois réduit sensiblement la facture sans rien perdre en
    qualité, car la correction d'un texte donné est déterministe.
    """
    cache_key = _correction_cache_key(message)
    try:
        cached = get_redis_sync().get(cache_key)
        if cached:
            return json.loads(cached)
    except Exception:  # noqa: BLE001 - cache indisponible : on continue sans
        logger.debug("Cache Redis indisponible pour la correction (fail-open).")

    try:
        response = _create_completion(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": CORRECTION_SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
    except (APIStatusError, *_RETRYABLE_ERRORS) as exc:
        logger.error("Échec de la correction LLM (message non corrigé) : %s", exc)
        return {"has_errors": False, "erreurs": []}

    raw = response.choices[0].message.content
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        logger.warning("Réponse LLM non-JSON pour la correction : %r", raw)
        data = {"has_errors": False, "erreurs": []}

    data.setdefault("erreurs", [])
    data.setdefault("has_errors", bool(data["erreurs"]))

    try:
        get_redis_sync().setex(cache_key, CORRECTION_CACHE_TTL_SECONDS, json.dumps(data))
    except Exception:  # noqa: BLE001
        logger.debug("Impossible d'écrire dans le cache Redis (fail-open).")

    return data
