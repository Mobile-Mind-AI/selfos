"""User-related models."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Time,
)
from sqlalchemy.orm import relationship

from .base import Base


class User(Base):
    __tablename__ = "users"
    uid = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)

    # Relationships - defined here but will reference models from other modules
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    projects = relationship(
        "Project", back_populates="user", cascade="all, delete-orphan"
    )
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    habits = relationship("Habit", back_populates="user", cascade="all, delete-orphan")
    habit_completions = relationship(
        "HabitCompletion", back_populates="user", cascade="all, delete-orphan"
    )
    life_areas = relationship(
        "LifeArea", back_populates="user", cascade="all, delete-orphan"
    )
    media_attachments = relationship(
        "MediaAttachment", back_populates="user", cascade="all, delete-orphan"
    )
    memory_items = relationship(
        "MemoryItem", back_populates="user", cascade="all, delete-orphan"
    )
    preferences = relationship(
        "UserPreferences",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    feedback_logs = relationship(
        "FeedbackLog", back_populates="user", cascade="all, delete-orphan"
    )
    story_sessions = relationship(
        "StorySession", back_populates="user", cascade="all, delete-orphan"
    )
    assistant_profiles = relationship(
        "AssistantProfile",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="AssistantProfile.user_id",
    )
    assistant_permissions = relationship(
        "AssistantPermission", back_populates="user", cascade="all, delete-orphan"
    )
    conversation_logs = relationship(
        "ConversationLog", back_populates="user", cascade="all, delete-orphan"
    )
    conversation_sessions = relationship(
        "ConversationSession", back_populates="user", cascade="all, delete-orphan"
    )
    intent_feedback = relationship(
        "IntentFeedback", back_populates="user", cascade="all, delete-orphan"
    )
    preferences_history = relationship(
        "UserPreferencesHistory", back_populates="user", cascade="all, delete-orphan"
    )
    journal_entries = relationship(
        "JournalEntry", back_populates="user", cascade="all, delete-orphan"
    )
    tags = relationship("Tag", back_populates="user", cascade="all, delete-orphan")
    entities = relationship(
        "Entity", back_populates="user", cascade="all, delete-orphan"
    )
    entity_types = relationship(
        "EntityType", back_populates="user", cascade="all, delete-orphan"
    )
    entity_relationships = relationship(
        "EntityRelationship", back_populates="user", cascade="all, delete-orphan"
    )
