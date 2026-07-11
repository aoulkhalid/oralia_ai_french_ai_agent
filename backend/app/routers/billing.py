"""
Scaffold freemium/premium (Phase 8).

IMPORTANT : ceci N'EST PAS une intégration de paiement réelle. Il n'existe
aucun moyen de facturer réellement un utilisateur ici — `/billing/upgrade`
bascule juste le champ `plan` en base, pour permettre de développer et
tester la logique différenciée free/premium (ex: limites de débit dans
core/redis_client.py) avant de brancher un vrai fournisseur de paiement.

Pour une vraie mise en production, il faudrait :
1. Choisir un fournisseur (Stripe est le plus courant pour du SaaS).
2. Remplacer POST /billing/upgrade par une redirection vers une session
   Stripe Checkout (stripe.checkout.Session.create(...)).
3. Ajouter un endpoint webhook (POST /billing/webhook) qui reçoit les
   événements Stripe (checkout.session.completed, customer.subscription.
   deleted, etc.) et met à jour user.plan en conséquence — c'est le
   webhook, jamais le navigateur, qui doit être la source de vérité pour
   activer/désactiver le plan premium.
4. Gérer les renouvellements/désabonnements/échecs de paiement via les
   webhooks `invoice.payment_failed` et `customer.subscription.updated`.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/plan")
def get_my_plan(current_user: User = Depends(get_current_user)):
    return {"plan": current_user.plan}


@router.post("/upgrade")
def upgrade_to_premium(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    ⚠️ DÉMONSTRATION UNIQUEMENT — bascule le plan sans paiement réel.
    À remplacer par une vraie intégration Stripe (ou autre) avant toute
    mise en production, sans quoi n'importe quel utilisateur authentifié
    peut s'auto-attribuer le plan premium gratuitement.
    """
    current_user.plan = "premium"
    db.commit()
    return {"plan": current_user.plan}


@router.post("/downgrade")
def downgrade_to_free(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.plan = "free"
    db.commit()
    return {"plan": current_user.plan}
