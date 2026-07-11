from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.database import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"), nullable=True)
    titre = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    # Re-added by migration 0004: chat.py's close_conversation() and
    # ConversationOut need a way to mark/expose when a conversation ended.
    ended_at = Column(DateTime(timezone=True), nullable=True)

    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
