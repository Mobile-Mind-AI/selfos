"""Journal entries model for personal reflections and daily logs."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .associations import journal_entry_tags
from .base import Base


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)

    # Entry content
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    mood = Column(String, nullable=True)  # happy, sad, neutral, excited, anxious, etc.
    mood_score = Column(Integer, nullable=True)  # 1-10 scale

    # Entry metadata
    entry_type = Column(
        String, nullable=False, default="reflection"
    )  # reflection, daily, goal_review, gratitude
    entry_date = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Related entities
    life_area_id = Column(Integer, ForeignKey("life_areas.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)

    # AI-extracted insights
    extracted_entities = Column(
        JSON, nullable=True
    )  # Extracted people, places, concepts
    sentiment_score = Column(
        JSON, nullable=True
    )  # {"positive": 0.7, "negative": 0.1, "neutral": 0.2}
    key_themes = Column(
        JSON, nullable=True
    )  # ["productivity", "relationships", "health"]

    # Privacy settings
    is_private = Column(Boolean, nullable=False, default=True)

    # Versioning for sync
    version = Column(Integer, nullable=False, default=1)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="journal_entries")
    life_area = relationship("LifeArea", back_populates="journal_entries")
    project = relationship("Project", back_populates="journal_entries")
    goal = relationship("Goal", back_populates="journal_entries")
    task = relationship("Task", back_populates="journal_entries")
    tags = relationship(
        "Tag", secondary=journal_entry_tags, back_populates="journal_entries"
    )
    media_attachments = relationship("MediaAttachment", back_populates="journal_entry")


# Performance indexes
Index("ix_journal_user_date", JournalEntry.user_id, JournalEntry.entry_date.desc())
Index("ix_journal_user_type", JournalEntry.user_id, JournalEntry.entry_type)
Index("ix_journal_life_area", JournalEntry.life_area_id, JournalEntry.entry_date.desc())
