"""
Service de persistance des conversations : création/récupération,
sauvegarde des messages et corrections, historique, mise à jour de
la progression de l'utilisateur.
"""

import json
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.correction import Correction
from app.models.progress import Progress
from app.models.niveau_historique import NiveauHistorique
from app.models.scenario import Scenario
from app.models.user import User

# Nombre de derniers messages envoyés au LLM comme contexte de conversation
MAX_HISTORY_MESSAGES = 12

# --- Progression de niveau CECRL (Phase 6) ---------------------------------
CEFR_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]
# Réévalue le niveau tous les N conversations terminées.
CONVERSATIONS_PER_LEVEL_CHECK = 5
# Si moins de X corrections en moyenne par message utilisateur sur la
# fenêtre récente, on considère que l'utilisateur maîtrise le niveau actuel.
ERROR_RATE_THRESHOLD_FOR_LEVEL_UP = 0.5

# --- Gamification (Phase 7) -------------------------------------------------
POINTS_PAR_MESSAGE_SANS_ERREUR = 2
POINTS_PAR_CONVERSATION_COMPLETEE = 10


def get_or_create_conversation(
    db: Session,
    user: User,
    conversation_id: int | None,
    scenario_id: int | None = None,
) -> Conversation:
    """Récupère une conversation existante (si elle appartient à l'utilisateur)
    ou en crée une nouvelle, éventuellement dans le contexte d'un scénario
    (Phase 7)."""
    if conversation_id is not None:
        conversation = (
            db.query(Conversation)
            .filter(
                Conversation.id == conversation_id,
                Conversation.user_id == user.id,
            )
            .first()
        )
        if conversation:
            return conversation

    # NB : Conversation n'a plus de colonne niveau_cecrl (le niveau est
    # toujours lu depuis l'utilisateur, cf. llm_service.generate_reply).
    conversation = Conversation(user_id=user.id, scenario_id=scenario_id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_scenario_context(db: Session, conversation: Conversation) -> str | None:
    """Retourne le contexte_prompt du scénario associé à la conversation,
    s'il y en a un (Phase 7)."""
    if not conversation.scenario_id:
        return None
    scenario = db.query(Scenario).filter(Scenario.id == conversation.scenario_id).first()
    return scenario.contexte_prompt if scenario else None


def get_recent_history(
    db: Session, conversation: Conversation, limit: int = MAX_HISTORY_MESSAGES
) -> list[dict]:
    """Retourne les derniers messages de la conversation, du plus ancien au
    plus récent, au format attendu par llm_service.generate_reply."""
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(limit)
        .all()
    )
    messages.reverse()
    return [{"role": m.role, "content": m.contenu} for m in messages]


def save_message(
    db: Session, conversation: Conversation, role: str, content: str
) -> Message:
    message = Message(conversation_id=conversation.id, role=role, contenu=content)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def save_corrections(
    db: Session, message: Message, correction_data: dict
) -> list[Correction]:
    """Enregistre les corrections détectées sur un message utilisateur."""
    corrections: list[Correction] = []
    for err in correction_data.get("erreurs", []):
        correction = Correction(
            message_id=message.id,
            erreur=err.get("erreur", ""),
            correction=err.get("correction", ""),
            explication=err.get("explication"),
            categorie=err.get("categorie"),
        )
        db.add(correction)
        corrections.append(correction)

    if corrections:
        db.commit()
        for c in corrections:
            db.refresh(c)
    return corrections


def update_progress(
    db: Session,
    user: User,
    nb_new_corrections: int,
    categories_erreurs: list[str | None],
) -> Progress:
    """Met à jour le tableau de bord de progression après un échange.

    NB : `erreurs_frequentes` est une colonne String (JSON sérialisé en
    texte), pas une colonne JSON native : on doit donc json.loads/json.dumps
    nous-mêmes.
    """
    progress = db.query(Progress).filter(Progress.user_id == user.id).first()
    if not progress:
        progress = Progress(user_id=user.id, niveau_estime=user.niveau_cecrl)
        db.add(progress)
        db.commit()
        db.refresh(progress)
        # Premier point de la courbe de progression : le niveau de départ.
        db.add(NiveauHistorique(user_id=user.id, niveau=progress.niveau_estime))
        db.commit()

    frequences: dict[str, int] = {}
    if progress.erreurs_frequentes:
        try:
            existing = json.loads(progress.erreurs_frequentes)
            frequences = {e["categorie"]: e["count"] for e in existing}
        except (json.JSONDecodeError, TypeError, KeyError):
            frequences = {}

    for categorie in categories_erreurs:
        if not categorie:
            continue
        frequences[categorie] = frequences.get(categorie, 0) + 1

    progress.erreurs_frequentes = json.dumps(
        sorted(
            [{"categorie": c, "count": n} for c, n in frequences.items()],
            key=lambda x: x["count"],
            reverse=True,
        )
    )
    progress.niveau_estime = progress.niveau_estime or user.niveau_cecrl

    # --- Gamification (Phase 7) ---
    if nb_new_corrections == 0:
        progress.points = (progress.points or 0) + POINTS_PAR_MESSAGE_SANS_ERREUR
    _update_streak(progress)

    db.commit()
    db.refresh(progress)
    return progress


def _update_streak(progress: Progress) -> None:
    """
    Met à jour la série de jours consécutifs d'activité (streak).
    - Même jour que la dernière activité : ne change rien (déjà comptée).
    - Jour suivant : incrémente la série.
    - Plus d'un jour d'écart : la série repart à 1 (elle est rompue).
    """
    today = datetime.now(timezone.utc).date()
    derniere = progress.derniere_activite

    if derniere == today:
        return
    if derniere is not None and (today - derniere).days == 1:
        progress.streak_jours = (progress.streak_jours or 0) + 1
    else:
        progress.streak_jours = 1
    progress.derniere_activite = today


def _maybe_advance_level(db: Session, user: User, progress: Progress) -> None:
    """
    Réévalue le niveau CECRL tous les CONVERSATIONS_PER_LEVEL_CHECK
    conversations terminées. Fait avancer d'un niveau si le taux
    d'erreurs récent est sous le seuil, et trace le changement dans
    niveau_historique pour le graphique de progression.

    Heuristique volontairement simple (taux d'erreurs par message sur les
    dernières conversations terminées) : ce n'est pas une évaluation
    linguistique rigoureuse, mais un signal suffisant pour donner à
    l'utilisateur un sentiment de progression tangible.
    """
    if progress.conversations_completees % CONVERSATIONS_PER_LEVEL_CHECK != 0:
        return

    niveau_actuel = progress.niveau_estime or user.niveau_cecrl or "A1"
    if niveau_actuel not in CEFR_LEVELS or niveau_actuel == CEFR_LEVELS[-1]:
        return  # Déjà au niveau maximum, ou niveau inconnu -> on ne touche à rien

    # Conversations terminées les plus récentes de l'utilisateur
    recent_conversations = (
        db.query(Conversation)
        .filter(
            Conversation.user_id == user.id,
            Conversation.ended_at.isnot(None),
        )
        .order_by(Conversation.ended_at.desc())
        .limit(CONVERSATIONS_PER_LEVEL_CHECK)
        .all()
    )
    conversation_ids = [c.id for c in recent_conversations]
    if not conversation_ids:
        return

    nb_messages_user = (
        db.query(Message)
        .filter(Message.conversation_id.in_(conversation_ids), Message.role == "user")
        .count()
    )
    if nb_messages_user == 0:
        return

    nb_corrections = (
        db.query(Correction)
        .join(Message, Correction.message_id == Message.id)
        .filter(Message.conversation_id.in_(conversation_ids))
        .count()
    )

    taux_erreur = nb_corrections / nb_messages_user
    if taux_erreur >= ERROR_RATE_THRESHOLD_FOR_LEVEL_UP:
        return  # Encore trop d'erreurs pour ce niveau : on ne monte pas

    nouveau_niveau = CEFR_LEVELS[CEFR_LEVELS.index(niveau_actuel) + 1]
    progress.niveau_estime = nouveau_niveau
    user.niveau_cecrl = nouveau_niveau
    db.add(NiveauHistorique(user_id=user.id, niveau=nouveau_niveau))
    db.commit()


def close_conversation(db: Session, conversation: Conversation) -> Conversation:
    """Marque une conversation comme terminée et incrémente le compteur
    de conversations complétées dans la progression de l'utilisateur."""
    conversation.ended_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(conversation)

    progress = (
        db.query(Progress).filter(Progress.user_id == conversation.user_id).first()
    )
    if progress:
        progress.conversations_completees = (progress.conversations_completees or 0) + 1
        progress.points = (progress.points or 0) + POINTS_PAR_CONVERSATION_COMPLETEE
        db.commit()
        db.refresh(progress)

        user = db.query(User).filter(User.id == conversation.user_id).first()
        if user:
            _maybe_advance_level(db, user, progress)

    return conversation


def get_progression_stats(db: Session, user_id: int) -> dict:
    """
    Statistiques enrichies pour le tableau de bord de progression
    (Phase 6) : historique de niveau CECRL + tendance des corrections
    par semaine, en plus des données déjà exposées par /progress/{id}.
    """
    historique = (
        db.query(NiveauHistorique)
        .filter(NiveauHistorique.user_id == user_id)
        .order_by(NiveauHistorique.created_at.asc())
        .all()
    )
    niveau_historique = [
        {"niveau": h.niveau, "date": h.created_at.isoformat() if h.created_at else None}
        for h in historique
    ]

    # Corrections groupées par semaine ISO (ex: "2026-W27"), pour tracer une
    # tendance dans le temps (idéalement décroissante = progression).
    corrections = (
        db.query(Correction.categorie, Message.created_at)
        .join(Message, Correction.message_id == Message.id)
        .join(Conversation, Message.conversation_id == Conversation.id)
        .filter(Conversation.user_id == user_id)
        .all()
    )
    par_semaine: dict[str, int] = {}
    for _categorie, created_at in corrections:
        if not created_at:
            continue
        year, week, _ = created_at.isocalendar()
        cle = f"{year}-W{week:02d}"
        par_semaine[cle] = par_semaine.get(cle, 0) + 1

    erreurs_par_semaine = [
        {"semaine": semaine, "count": count}
        for semaine, count in sorted(par_semaine.items())
    ]

    return {
        "niveau_historique": niveau_historique,
        "erreurs_par_semaine": erreurs_par_semaine,
    }


# --- Badges (Phase 7 gamification) ------------------------------------------
# Calculés à la volée à partir des stats existantes plutôt que stockés :
# évite une table dédiée pour un besoin simple, et les critères peuvent
# évoluer sans migration.
def compute_badges(progress: Progress) -> list[dict]:
    badges = []
    if (progress.streak_jours or 0) >= 3:
        badges.append({"id": "streak_3", "label": "🔥 3 jours de suite", "description": "Pratique 3 jours consécutifs"})
    if (progress.streak_jours or 0) >= 7:
        badges.append({"id": "streak_7", "label": "🔥🔥 Une semaine de suite", "description": "Pratique 7 jours consécutifs"})
    if (progress.conversations_completees or 0) >= 1:
        badges.append({"id": "first_conversation", "label": "💬 Première conversation", "description": "A terminé sa première conversation"})
    if (progress.conversations_completees or 0) >= 10:
        badges.append({"id": "conversations_10", "label": "🗣️ Bavard·e", "description": "10 conversations complétées"})
    if (progress.points or 0) >= 100:
        badges.append({"id": "points_100", "label": "⭐ 100 points", "description": "A cumulé 100 points"})
    return badges
