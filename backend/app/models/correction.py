from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Correction(Base):
    __tablename__ = "corrections"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"), nullable=False, unique=True)
    erreur = Column(String, nullable=False)
    correction = Column(String, nullable=False)
    explication = Column(String, nullable=True)
    categorie = Column(String, nullable=True)  # ex: "grammaire", "conjugaison", "vocabulaire"

    message = relationship("Message", back_populates="correction")