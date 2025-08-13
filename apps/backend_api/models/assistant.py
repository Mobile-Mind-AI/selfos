"""
Assistant models for SelfOS Backend API.
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, JSON, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from .base import Base


class AssistantProfile(Base):
    __tablename__ = "assistant_profiles"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    
    # Profile configuration
    name = Column(String, nullable=False, default="Assistant")
    personality = Column(String, nullable=False, default="helpful")  # helpful, coach, friend, mentor
    voice_id = Column(String, nullable=True)  # For TTS integration
    avatar_url = Column(String, nullable=True)  # Custom avatar image
    
    # Behavior settings
    response_style = Column(String, nullable=False, default="balanced")  # concise, balanced, detailed
    encouragement_level = Column(String, nullable=False, default="medium")  # low, medium, high
    formality_level = Column(String, nullable=False, default="casual")  # casual, balanced, formal
    
    # Specialized knowledge areas
    expertise_areas = Column(JSON, nullable=False, default=list)  # ["productivity", "wellness", "motivation"]
    
    # Custom instructions
    custom_instructions = Column(Text, nullable=True)  # User-defined instructions for the assistant
    
    # Interaction history
    total_interactions = Column(Integer, nullable=False, default=0)
    last_interaction_at = Column(DateTime, nullable=True)
    
    # Active state
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="assistant_profiles")

# Performance indexes for AssistantProfile model
Index('ix_assistant_profiles_user_active', AssistantProfile.user_id, AssistantProfile.is_active)
Index('ix_assistant_profiles_user_created', AssistantProfile.user_id, AssistantProfile.created_at.desc())
