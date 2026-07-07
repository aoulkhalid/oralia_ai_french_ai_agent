from sqlalchemy import Column, Integer, String
from app.database import Base


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    niveau_cecrl = Column(String, nullable=False)
    categorie = Column(String, nullable=True)  # ex: "conjugaison", "vocabulaire"
    question = Column(String, nullable=False)
    reponse_attendue = Column(String, nullable=False)
