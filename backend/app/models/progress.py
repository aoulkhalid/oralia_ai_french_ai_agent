from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from app.database import Base


class Progress(Base):
    __tablename__ = "progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    niveau_estime = Column(String, nullable=True)
    conversations_completees = Column(Integer, default=0)
    erreurs_frequentes = Column(String, nullable=True)  # JSON stocké en texte, ou passer à JSONB plus tard
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())