from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from app.database import Base


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    # Nullable : un exercice peut être générique (banque commune) ou
    # personnalisé pour un utilisateur précis (généré par le LLM à partir
    # de ses erreurs fréquentes, cf. exercise_service.py).
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    niveau_cecrl = Column(String, nullable=False)
    categorie = Column(String, nullable=True)  # ex: "conjugaison", "vocabulaire"
    question = Column(String, nullable=False)
    reponse_attendue = Column(String, nullable=False)
    # Suivi de la tentative de l'utilisateur (Phase 7)
    reponse_utilisateur = Column(String, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
