"""
MemoryItem model for SelfOS Backend API.
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base


class MemoryItem(Base):
    __tablename__ = "memory_items"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="memory_items")

# Performance indexes for MemoryItem model
Index('ix_memory_user_timestamp', MemoryItem.user_id, MemoryItem.timestamp.desc())
