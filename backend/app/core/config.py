import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Paramètres de sécurité/auth lus depuis les variables d'environnement."""

    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-moi-en-production")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")  # 24h par défaut
    )


settings = Settings()