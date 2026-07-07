from sqlalchemy import Column, Integer, String
from app.database import Base


class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(Integer, primary_key=True, index=True)
    titre = Column(String, nullable=False)
    description = Column(String, nullable=True)
    niveau_cecrl = Column(String, nullable=True)
    contexte_prompt = Column(String, nullable=True)  # instructions pour orienter le LLM
