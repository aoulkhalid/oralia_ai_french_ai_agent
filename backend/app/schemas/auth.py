from pydantic import BaseModel


class Token(BaseModel):
    """Réponse renvoyée par POST /auth/login."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Contenu décodé du JWT (usage interne)."""

    email: str | None = None