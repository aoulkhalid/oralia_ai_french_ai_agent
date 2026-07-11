from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # "user" ou "assistant"
    contenu = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")
    # Un message utilisateur peut contenir plusieurs erreurs -> plusieurs
    # Correction. (La contrainte unique sur corrections.message_id, qui
    # limitait à une seule correction par message, est supprimée par la
    # migration 0004.)
    corrections = relationship(
        "Correction", back_populates="message", cascade="all, delete-orphan"
    )
