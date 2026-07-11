from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict, Field, field_validator


class UserCreate(BaseModel):
    """Payload pour POST /auth/register."""

    email: EmailStr
    password: str = Field(min_length=8, description="Minimum 8 caractères")
    nom: str | None = None
    niveau_cecrl: str = "A1"

    @field_validator("password")
    @classmethod
    def password_must_be_reasonably_strong(cls, v: str) -> str:
        # Renforcement Phase 8 : un mot de passe uniquement numérique ou
        # uniquement alphabétique est trop faible pour un compte réel.
        if not any(c.isalpha() for c in v) or not any(c.isdigit() for c in v):
            raise ValueError(
                "Le mot de passe doit contenir au moins une lettre et un chiffre."
            )
        return v


class UserOut(BaseModel):
    """Représentation publique d'un utilisateur (jamais le mot de passe)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    nom: str | None = None
    niveau_cecrl: str
    is_active: bool
    role: str = "student"
    plan: str = "free"
    created_at: datetime
