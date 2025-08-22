"""
Task model for SelfOS Backend API.
"""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .associations import task_entities, task_tags
from .base import Base


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    life_area_id = Column(Integer, ForeignKey("life_areas.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    # When task is due
    due_date = Column(DateTime)
    # Expected duration in minutes
    duration = Column(Integer)
    # Status: todo, in_progress, completed
    status = Column(String, nullable=False, default="todo")
    # Progress percentage 0.0 - 100.0
    progress = Column(Float, nullable=False, default=0.0)
    # List of prerequisite task IDs (kept as JSON for simplicity)
    dependencies = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="tasks")
    goal = relationship("Goal", back_populates="tasks")
    project = relationship("Project", back_populates="tasks")
    life_area = relationship("LifeArea", back_populates="tasks")
    media_attachments = relationship("MediaAttachment", back_populates="task")
    journal_entries = relationship("JournalEntry", back_populates="task")

    # Many-to-many relationship with entities
    entities = relationship("Entity", secondary=task_entities, backref="tasks")

    # Many-to-many relationship with tags
    tags = relationship("Tag", secondary=task_tags, back_populates="tasks")


# Performance indexes for Task model
Index("ix_tasks_user_created", Task.user_id, Task.created_at.desc())
Index("ix_tasks_user_status", Task.user_id, Task.status)
Index("ix_tasks_goal_created", Task.goal_id, Task.created_at.desc())
Index("ix_tasks_project_created", Task.project_id, Task.created_at.desc())
Index("ix_tasks_due_date", Task.user_id, Task.due_date)
# Partial index for completed tasks (PostgreSQL specific, will be in migration)
Index(
    "ix_tasks_completed",
    Task.user_id,
    Task.created_at.desc(),
    postgresql_where=(Task.status == "completed"),
)
