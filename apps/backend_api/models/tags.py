"""Tag system models for flexible cross-context entity grouping."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from .associations import (
    goal_tags,
    habit_tags,
    journal_entry_tags,
    project_tags,
    task_tags,
)
from .base import Base


class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    name = Column(String, nullable=False)
    color = Column(String)  # Hex color code for UI (e.g., "#FF5722")

    # Versioning for sync
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="tags")

    # Many-to-many relationships with all entities
    projects = relationship("Project", secondary=project_tags, back_populates="tags")
    goals = relationship("Goal", secondary=goal_tags, back_populates="tags")
    tasks = relationship("Task", secondary=task_tags, back_populates="tags")
    habits = relationship("Habit", secondary=habit_tags, back_populates="tags")
    journal_entries = relationship(
        "JournalEntry", secondary=journal_entry_tags, back_populates="tags"
    )

    # Ensure unique tag names per user
    __table_args__ = (Index("uq_user_tag_name", "user_id", "name", unique=True),)
