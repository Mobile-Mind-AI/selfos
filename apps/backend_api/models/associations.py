"""
Association tables for many-to-many relationships.
Centralized to avoid circular import issues.
"""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Table

from .base import Base

# Tag association tables
project_tags = Table(
    "project_tags",
    Base.metadata,
    Column(
        "project_id",
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    ),
)

goal_tags = Table(
    "goal_tags",
    Base.metadata,
    Column(
        "goal_id", Integer, ForeignKey("goals.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    ),
)

task_tags = Table(
    "task_tags",
    Base.metadata,
    Column(
        "task_id", Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    ),
)

habit_tags = Table(
    "habit_tags",
    Base.metadata,
    Column(
        "habit_id",
        Integer,
        ForeignKey("habits.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    ),
)

journal_entry_tags = Table(
    "journal_entry_tags",
    Base.metadata,
    Column(
        "journal_entry_id",
        Integer,
        ForeignKey("journal_entries.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    ),
)

# Entity association tables
goal_entities = Table(
    "goal_entities",
    Base.metadata,
    Column(
        "goal_id", Integer, ForeignKey("goals.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "entity_id",
        Integer,
        ForeignKey("entities.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("created_at", DateTime, default=datetime.utcnow),
    Index("ix_goal_entities_goal", "goal_id"),
    Index("ix_goal_entities_entity", "entity_id"),
)

project_entities = Table(
    "project_entities",
    Base.metadata,
    Column(
        "project_id",
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "entity_id",
        Integer,
        ForeignKey("entities.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("created_at", DateTime, default=datetime.utcnow),
    Index("ix_project_entities_project", "project_id"),
    Index("ix_project_entities_entity", "entity_id"),
)

task_entities = Table(
    "task_entities",
    Base.metadata,
    Column(
        "task_id", Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True
    ),
    Column(
        "entity_id",
        Integer,
        ForeignKey("entities.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("created_at", DateTime, default=datetime.utcnow),
    Index("ix_task_entities_task", "task_id"),
    Index("ix_task_entities_entity", "entity_id"),
)
