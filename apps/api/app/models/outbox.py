from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import JSONB

from ..db import Base
from .core import ulid


class OutboxEvent(Base):
    __tablename__ = "events"
    __table_args__ = {"schema": "outbox"}

    id = Column(String, primary_key=True, default=ulid)
    event_type = Column(String, nullable=False)
    aggregate_type = Column(String, nullable=True)
    aggregate_id = Column(String, nullable=True)
    payload = Column(JSONB, nullable=False, default=dict)
    status = Column(String, nullable=False, default="pending")
    attempts = Column(Integer, nullable=False, default=0)
    next_attempt_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

