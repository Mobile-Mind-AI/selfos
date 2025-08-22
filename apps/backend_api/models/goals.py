"""Goal model for hierarchical goal tracking."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from .associations import goal_tags
from .base import Base


class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    life_area_id = Column(Integer, ForeignKey("life_areas.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    parent_id = Column(Integer, ForeignKey("goals.id"), nullable=True)

    title = Column(String, nullable=False)
    description = Column(Text)

    # Status: e.g., todo, in_progress, completed
    status = Column(String, nullable=False, default="todo")

    # Progress percentage 0.0 - 100.0
    progress = Column(Float, nullable=False, default=0.0)

    # Target date for completion
    target_date = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Versioning for sync
    version = Column(Integer, nullable=False, default=1)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="goals")
    life_area = relationship("LifeArea", back_populates="goals")
    project = relationship("Project", back_populates="goals")
    tasks = relationship("Task", back_populates="goal", cascade="all, delete-orphan")
    habits = relationship("Habit", back_populates="goal")
    media_attachments = relationship("MediaAttachment", back_populates="goal")
    entities = relationship("Entity", secondary="goal_entities")
    journal_entries = relationship("JournalEntry", back_populates="goal")

    # Hierarchical relationships
    parent = relationship("Goal", remote_side=[id], back_populates="children")
    children = relationship(
        "Goal", back_populates="parent", cascade="all, delete-orphan"
    )

    # Many-to-many relationship with tags
    tags = relationship("Tag", secondary=goal_tags, back_populates="goals")


# Performance indexes for Goal model
Index("ix_goals_user_created", Goal.user_id, Goal.created_at.desc())
Index("ix_goals_user_status", Goal.user_id, Goal.status)
Index("ix_goals_life_area_created", Goal.life_area_id, Goal.created_at.desc())
Index("ix_goals_project_created", Goal.project_id, Goal.created_at.desc())
Index("ix_goals_parent_id", Goal.parent_id)
Index("ix_goals_user_parent", Goal.user_id, Goal.parent_id)
