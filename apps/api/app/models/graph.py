from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import JSONB

from ..db import Base
from .core import ulid


class GraphNode(Base):
    __tablename__ = "nodes"
    __table_args__ = {"schema": "graph"}

    id = Column(String, primary_key=True, default=ulid)
    type = Column(String, nullable=False)
    label = Column(String, nullable=False)
    aliases = Column(JSONB, nullable=False, default=list)


class GraphEdge(Base):
    __tablename__ = "edges"
    __table_args__ = {"schema": "graph"}

    # composite PK emulated with unique index in migration; for now simple id
    id = Column(String, primary_key=True, default=ulid)
    src_type = Column(String, nullable=False)
    src_id = Column(String, nullable=False)
    rel = Column(String, nullable=False)
    dst_type = Column(String, nullable=False)
    dst_id = Column(String, nullable=False)
    weight = Column(Integer, nullable=True)
    props = Column(JSONB, nullable=False, default=dict)

