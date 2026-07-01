from sqlalchemy import Column, Integer, String, DateTime, func
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    nom = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    niveau_cecrl = Column(String, default="A1")
    created_at = Column(DateTime(timezone=True), server_default=func.now())