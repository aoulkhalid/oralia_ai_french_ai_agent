from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.config import settings
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
)
from app.core.deps import get_current_user
from app.core.redis_client import rate_limiter_by_ip
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.correction import Correction
from app.models.progress import Progress
from app.models.niveau_historique import NiveauHistorique
from app.models.exercise import Exercise
from app.schemas.user import UserCreate, UserOut
from app.schemas.auth import Token

router = APIRouter(prefix="/auth", tags=["auth"])

# Protection anti brute-force / anti spam (Phase 8) : ces routes ne sont
# pas encore authentifiées, donc le rate limiting se fait par IP plutôt
# que par utilisateur.
_register_rate_limit = rate_limiter_by_ip("auth-register", limit_per_minute=5)
_login_rate_limit = rate_limiter_by_ip("auth-login", limit_per_minute=10)


@router.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_register_rate_limit)],
)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    """Crée un nouveau compte utilisateur."""
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un compte existe déjà avec cet email.",
        )

    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        nom=payload.nom,
        niveau_cecrl=payload.niveau_cecrl,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Initialise le tableau de bord de progression associé
    # (Progress.niveau_estime remplace l'ancien Progress.niveau_actuel)
    progress = Progress(user_id=user.id, niveau_estime=user.niveau_cecrl)
    db.add(progress)
    db.commit()

    # Premier point de la courbe de progression CECRL (Phase 6). NB : avant
    # ce correctif, ce point n'était créé que lors du premier message de
    # chat (dans update_progress), mais celui-ci trouvait toujours un
    # Progress déjà existant (créé ici) et sautait donc la création de
    # l'historique — le graphique de progression partait alors sans point
    # de départ visible.
    db.add(NiveauHistorique(user_id=user.id, niveau=user.niveau_cecrl))
    db.commit()

    return user


@router.post("/login", response_model=Token, dependencies=[Depends(_login_rate_limit)])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    Authentifie un utilisateur et renvoie un JWT.
    Utilise OAuth2PasswordRequestForm : le champ `username` correspond à l'email.
    """
    user = db.query(User).filter(User.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Compte utilisateur désactivé.")

    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserOut)
def read_current_user(current_user: User = Depends(get_current_user)):
    """Retourne le profil de l'utilisateur authentifié."""
    return current_user


# ---------------------------------------------------------------------------
# RGPD (Phase 8) : droit d'accès (export) et droit à l'effacement (suppression)
# ---------------------------------------------------------------------------
# NB : ces deux endpoints fournissent les MÉCANISMES techniques attendus
# par le RGPD (portabilité des données, droit à l'oubli). La conformité
# RGPD complète implique aussi des obligations non techniques (politique
# de confidentialité, registre de traitement, base légale documentée,
# désignation d'un DPO le cas échéant) qui restent à votre charge.


@router.get("/me/data-export")
def export_my_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Exporte toutes les données personnelles de l'utilisateur (droit d'accès RGPD)."""
    conversations = (
        db.query(Conversation).filter(Conversation.user_id == current_user.id).all()
    )
    conversation_ids = [c.id for c in conversations]
    messages = (
        db.query(Message).filter(Message.conversation_id.in_(conversation_ids)).all()
        if conversation_ids
        else []
    )
    message_ids = [m.id for m in messages]
    corrections = (
        db.query(Correction).filter(Correction.message_id.in_(message_ids)).all()
        if message_ids
        else []
    )
    progress = db.query(Progress).filter(Progress.user_id == current_user.id).first()
    exercises = db.query(Exercise).filter(Exercise.user_id == current_user.id).all()

    return {
        "profil": {
            "id": current_user.id,
            "email": current_user.email,
            "nom": current_user.nom,
            "niveau_cecrl": current_user.niveau_cecrl,
            "role": current_user.role,
            "plan": current_user.plan,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
        "conversations": [
            {
                "id": c.id,
                "titre": c.titre,
                "scenario_id": c.scenario_id,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "ended_at": c.ended_at.isoformat() if c.ended_at else None,
            }
            for c in conversations
        ],
        "messages": [
            {
                "id": m.id,
                "conversation_id": m.conversation_id,
                "role": m.role,
                "contenu": m.contenu,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
        "corrections": [
            {
                "id": c.id,
                "message_id": c.message_id,
                "erreur": c.erreur,
                "correction": c.correction,
                "categorie": c.categorie,
            }
            for c in corrections
        ],
        "progression": {
            "niveau_estime": progress.niveau_estime if progress else None,
            "conversations_completees": progress.conversations_completees if progress else 0,
            "points": progress.points if progress else 0,
            "streak_jours": progress.streak_jours if progress else 0,
        }
        if progress
        else None,
        "exercices": [
            {
                "id": e.id,
                "question": e.question,
                "reponse_utilisateur": e.reponse_utilisateur,
                "is_correct": e.is_correct,
            }
            for e in exercises
        ],
    }


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Supprime définitivement le compte et toutes les données associées
    (droit à l'effacement RGPD). Irréversible.
    """
    conversation_ids = [
        c.id
        for c in db.query(Conversation.id).filter(Conversation.user_id == current_user.id).all()
    ]
    if conversation_ids:
        message_ids = [
            m.id
            for m in db.query(Message.id)
            .filter(Message.conversation_id.in_(conversation_ids))
            .all()
        ]
        if message_ids:
            db.query(Correction).filter(Correction.message_id.in_(message_ids)).delete(
                synchronize_session=False
            )
        db.query(Message).filter(Message.conversation_id.in_(conversation_ids)).delete(
            synchronize_session=False
        )
        db.query(Conversation).filter(Conversation.user_id == current_user.id).delete(
            synchronize_session=False
        )

    db.query(Exercise).filter(Exercise.user_id == current_user.id).delete(synchronize_session=False)
    db.query(NiveauHistorique).filter(NiveauHistorique.user_id == current_user.id).delete(
        synchronize_session=False
    )
    db.query(Progress).filter(Progress.user_id == current_user.id).delete(synchronize_session=False)
    db.query(User).filter(User.id == current_user.id).delete(synchronize_session=False)

    db.commit()
    return None
