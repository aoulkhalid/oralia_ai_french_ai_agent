from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, func
from app.database import Base


class Progress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    niveau_estime = Column(String, nullable=True)
    conversations_completees = Column(Integer, default=0)
    # JSON stocké en texte (colonne String) : on sérialise/désérialise
    # nous-mêmes avec json.dumps / json.loads dans conversation_service.py.
    erreurs_frequentes = Column(String, nullable=True)
    # --- Gamification (Phase 7) ---
    points = Column(Integer, default=0, nullable=False)
    streak_jours = Column(Integer, default=0, nullable=False)
    derniere_activite = Column(Date, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
