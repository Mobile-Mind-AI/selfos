from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB

from ..db import Base
from .core import ulid


class AuditEvent(Base):
    __tablename__ = "events"
    __table_args__ = {"schema": "audit"}

    id = Column(String, primary_key=True, default=ulid)
    user_id = Column(String, nullable=True)
    action = Column(String, nullable=False)
    ref_type = Column(String, nullable=True)
    ref_id = Column(String, nullable=True)
    meta = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

