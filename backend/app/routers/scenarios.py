from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.scenario import Scenario
from app.schemas.scenario import ScenarioOut

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioOut])
def list_scenarios(
    categorie: str | None = None,
    niveau_cecrl: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Liste les scénarios de conversation disponibles (Phase 7), avec
    filtres optionnels par catégorie ("quotidien", "delf", "tcf",
    "professionnel") et par niveau CECRL.
    """
    query = db.query(Scenario)
    if categorie:
        query = query.filter(Scenario.categorie == categorie)
    if niveau_cecrl:
        query = query.filter(Scenario.niveau_cecrl == niveau_cecrl)
    return query.order_by(Scenario.id.asc()).all()


@router.get("/{scenario_id}", response_model=ScenarioOut)
def get_scenario(
    scenario_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scenario = db.query(Scenario).filter(Scenario.id == scenario_id).first()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scénario introuvable.")
    return scenario
