from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB

from ..db import Base
from .core import ulid


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = {"schema": "chat"}

    id = Column(String, primary_key=True, default=ulid)
    user_id = Column(String, nullable=False)
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = {"schema": "chat"}

    id = Column(String, primary_key=True, default=ulid)
    conversation_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    role = Column(String, nullable=False)  # user|assistant|system
    content = Column(String, nullable=False)
    extracted = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

