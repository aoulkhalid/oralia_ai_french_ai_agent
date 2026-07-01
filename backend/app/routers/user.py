from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    nom = Column(String, nullable=True)
    niveau_cecrl = Column(String, default="A1")  # A1, A2, B1, B2, C1, C2
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversations = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )
    progress = relationship(
        "Progress", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )