"""
Assistant models for SelfOS Backend API.
"""

from datetime import datetime
from uuid import uuid4

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

from .base import Base


class AssistantProfile(Base):
    __tablename__ = "assistant_profiles"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    owner_id = Column(
        String, ForeignKey("users.uid"), nullable=False
    )  # Who owns this assistant

    # Basic configuration
    name = Column(String, nullable=False, default="Assistant")
    description = Column(String, nullable=True)  # Assistant description
    avatar_url = Column(String, nullable=True)  # Custom avatar image

    # AI model settings
    ai_model = Column(
        String, nullable=False, default="gpt-3.5-turbo"
    )  # AI model to use
    language = Column(String, nullable=False, default="en")  # Primary language

    # Behavior settings
    requires_confirmation = Column(
        Boolean, nullable=False, default=True
    )  # Require user confirmation
    style = Column(
        JSON,
        nullable=False,
        default=lambda: {
            "formality": 50,
            "directness": 50,
            "humor": 30,
            "empathy": 70,
            "motivation": 60,
        },
    )  # PersonalityStyle configuration
    dialogue_temperature = Column(
        JSON, nullable=False, default=0.8
    )  # Temperature for dialogue
    intent_temperature = Column(
        JSON, nullable=False, default=0.3
    )  # Temperature for intent

    # Custom instructions
    custom_instructions = Column(
        Text, nullable=True
    )  # User-defined instructions for the assistant

    # Profile state
    is_default = Column(
        Boolean, nullable=False, default=False
    )  # Default assistant for user
    is_public = Column(Boolean, nullable=False, default=False)  # Public assistant
    is_active = Column(Boolean, nullable=False, default=True)  # Active state

    # Version tracking
    version = Column(Integer, nullable=False, default=1000)  # Version number for sync

    # Interaction history
    total_interactions = Column(Integer, nullable=False, default=0)
    last_interaction_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship(
        "User", back_populates="assistant_profiles", foreign_keys=[user_id]
    )
    permissions = relationship(
        "AssistantPermission", back_populates="assistant", cascade="all, delete-orphan"
    )


# Performance indexes for AssistantProfile model
Index(
    "ix_assistant_profiles_user_active",
    AssistantProfile.user_id,
    AssistantProfile.is_active,
)
Index(
    "ix_assistant_profiles_user_created",
    AssistantProfile.user_id,
    AssistantProfile.created_at.desc(),
)
