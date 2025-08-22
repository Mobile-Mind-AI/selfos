"""
LifeArea model for SelfOS Backend API.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from .base import Base


class LifeArea(Base):
    __tablename__ = "life_areas"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    name = Column(String, nullable=False)
    # Weight as percentage importance (0-100)
    weight = Column(Integer, default=10, nullable=False)
    # Optional UI icon identifier
    icon = Column(String)
    # UI color preference (hex color or color name)
    color = Column(String)
    # Description of this life area
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="life_areas")
    goals = relationship("Goal", back_populates="life_area")
    projects = relationship("Project", back_populates="life_area")
    tasks = relationship("Task", back_populates="life_area")
    habits = relationship("Habit", back_populates="life_area")
    journal_entries = relationship("JournalEntry", back_populates="life_area")


# Performance indexes for LifeArea model
Index("ix_life_areas_user_created", LifeArea.user_id, LifeArea.created_at.desc())
Index("ix_life_areas_user_name", LifeArea.user_id, LifeArea.name)
