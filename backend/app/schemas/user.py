from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict, Field


class UserCreate(BaseModel):
    """Payload pour POST /auth/register."""

    email: EmailStr
    password: str = Field(min_length=8, description="Minimum 8 caractères")
    nom: str | None = None
    niveau_cecrl: str = "A1"


class UserOut(BaseModel):
    """Représentation publique d'un utilisateur (jamais le mot de passe)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    nom: str | None = None
    niveau_cecrl: str
    is_active: bool
    created_at: datetime