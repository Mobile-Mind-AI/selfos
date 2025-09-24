from datetime import datetime

from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import JSONB

from ..db import Base
from .core import ulid


class Memory(Base):
    __tablename__ = "memories"
    __table_args__ = {"schema": "memory"}

    id = Column(String, primary_key=True, default=ulid)
    user_id = Column(String, nullable=False)  # schema-agnostic; reference core.users.id in app logic
    text = Column(String, nullable=False)
    # embedding stored via pgvector; managed in migration as raw SQL
    metadata = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

