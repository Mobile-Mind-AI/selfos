from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB

from ..db import Base
from .core import ulid


class Agent(Base):
    __tablename__ = "agents"
    __table_args__ = {"schema": "agent"}

    id = Column(String, primary_key=True, default=ulid)
    user_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    type = Column(String, nullable=False)  # life_coach, fitness, etc.
    scopes = Column(JSONB, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class AgentRun(Base):
    __tablename__ = "runs"
    __table_args__ = {"schema": "agent"}

    id = Column(String, primary_key=True, default=ulid)
    agent_id = Column(String, nullable=False)
    user_id = Column(String, nullable=False)
    input = Column(JSONB, nullable=False, default=dict)
    output = Column(JSONB, nullable=False, default=dict)
    status = Column(String, nullable=False, default="completed")
    costs = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

