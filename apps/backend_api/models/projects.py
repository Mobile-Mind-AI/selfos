"""
Project model for SelfOS Backend API.
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

from .associations import project_entities, project_tags
from .base import Base


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    life_area_id = Column(Integer, ForeignKey("life_areas.id"), nullable=True)
    parent_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    # Status: e.g., todo, in_progress, completed, paused
    status = Column(String, nullable=False, default="todo")
    # Progress percentage 0.0 - 100.0
    progress = Column(Float, nullable=False, default=0.0)
    # Optional start and end dates for the project
    start_date = Column(DateTime)
    target_date = Column(DateTime)
    # Project priority: low, medium, high
    priority = Column(String, nullable=False, default="medium")
    # Project phases/milestones as JSON
    phases = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="projects")
    life_area = relationship("LifeArea", back_populates="projects")
    goals = relationship("Goal", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    media_attachments = relationship("MediaAttachment", back_populates="project")
    journal_entries = relationship("JournalEntry", back_populates="project")

    # Hierarchical relationships
    parent = relationship("Project", remote_side=[id], back_populates="children")
    children = relationship(
        "Project", back_populates="parent", cascade="all, delete-orphan"
    )

    # Many-to-many relationship with entities
    entities = relationship("Entity", secondary=project_entities, backref="projects")

    # Many-to-many relationship with tags
    tags = relationship("Tag", secondary=project_tags, back_populates="projects")


# Performance indexes for Project model
Index("ix_projects_user_created", Project.user_id, Project.created_at.desc())
Index("ix_projects_user_status", Project.user_id, Project.status)
Index("ix_projects_life_area_created", Project.life_area_id, Project.created_at.desc())
Index("ix_projects_user_priority", Project.user_id, Project.priority)
