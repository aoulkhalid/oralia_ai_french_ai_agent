from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings

# ---------------------------------------------------------------------------
# Mots de passe (bcrypt)
# ---------------------------------------------------------------------------


def get_password_hash(password: str) -> str:
    """Hache un mot de passe en clair avec bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie qu'un mot de passe en clair correspond au hash stocké."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


# ---------------------------------------------------------------------------
# JSON Web Tokens
# ---------------------------------------------------------------------------


def create_access_token(
    data: dict, expires_delta: timedelta | None = None
) -> str:
    """Crée un JWT signé contenant `data` (ex: {"sub": user_email})."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Décode et valide un JWT. Lève jwt.PyJWTError si invalide/expiré."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])