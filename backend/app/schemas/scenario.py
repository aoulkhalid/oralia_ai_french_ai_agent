from pydantic import BaseModel, ConfigDict


class ScenarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titre: str
    description: str | None = None
    niveau_cecrl: str | None = None
    categorie: str | None = None
