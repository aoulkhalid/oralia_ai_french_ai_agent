from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.database import Base


class NiveauHistorique(Base):
    """Trace chaque changement de niveau CECRL d'un utilisateur, pour
    pouvoir tracer une courbe de progression dans le temps (Phase 6)."""

    __tablename__ = "niveau_historique"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    niveau = Column(String, nullable=False)  # A1..C2
    created_at = Column(DateTime(timezone=True), server_default=func.now())
