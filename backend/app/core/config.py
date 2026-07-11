"""
Configuration centralisée de l'application, lue depuis les variables
d'environnement (voir backend/.env.example).

Avant : la config JWT (config.py) et l'URL de la base de données
(database.py) étaient lues indépendamment via os.getenv() + load_dotenv()
dupliqué dans deux fichiers, sans validation ni valeurs par défaut sûres.
Maintenant : une seule source de vérité (Settings), avec pydantic-settings
qui valide les types au démarrage (échoue vite et clairement si une valeur
est incorrecte, plutôt que de planter plus tard au premier appel réseau).
"""
import logging
import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("app.config")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Base de données ---
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/francais_ia"

    # --- Redis (cache + rate limiting) ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Sécurité / JWT ---
    # Pas de valeur par défaut "réelle" en dur : si absente, on génère une
    # clé aléatoire au démarrage (utilisable en dev, mais invalide les
    # tokens à chaque redémarrage) et on avertit bien fort, plutôt que de
    # signer silencieusement les tokens avec un secret prévisible.
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # --- LLM (compatible OpenAI : Groq, DeepSeek, Ollama, etc.) ---
    # Le SDK OpenAI est utilisé pour parler à n'importe quel fournisseur
    # exposant une API compatible OpenAI ; il suffit de changer BASE_URL,
    # MODEL et API_KEY pour changer de fournisseur, sans toucher au code.
    # Valeurs par défaut ci-dessous : Groq (gratuit, tier gratuit généreux).
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.groq.com/openai/v1"
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TIMEOUT_SECONDS: float = 30.0
    LLM_MAX_RETRIES: int = 3

    # --- CORS ---
    # Liste séparée par des virgules, ex: "http://localhost:3000,https://mondomaine.com"
    CORS_ORIGINS: str = "http://localhost:3000"

    # --- Rate limiting (Redis) ---
    CHAT_RATE_LIMIT_PER_MINUTE: int = 20
    SPEECH_RATE_LIMIT_PER_MINUTE: int = 10

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()

if not settings.JWT_SECRET_KEY or settings.JWT_SECRET_KEY in {
    "change-moi-en-production",
    "12343445567890987",
}:
    logger.warning(
        "JWT_SECRET_KEY n'est pas défini (ou utilise une valeur d'exemple connue) : "
        "définissez JWT_SECRET_KEY dans backend/.env avant la mise en production."
    )

if not settings.LLM_API_KEY:
    logger.warning(
        "LLM_API_KEY n'est pas défini : les fonctionnalités de chat "
        "IA échoueront tant que cette variable n'est pas configurée."
    )
