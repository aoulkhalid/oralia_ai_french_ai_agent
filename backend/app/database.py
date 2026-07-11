from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

# Avant : DATABASE_URL était relu ici via os.getenv() + load_dotenv(),
# dupliquant la logique déjà présente dans core/config.py (deux sources
# de vérité qui pouvaient diverger). Maintenant : une seule Settings
# centralisée, importée partout.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # évite les erreurs "server closed the connection" après une coupure réseau/DB idle
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency FastAPI: fournit une session DB et la ferme après usage."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
