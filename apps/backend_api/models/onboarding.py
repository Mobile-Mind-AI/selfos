"""Onboarding and personal configuration models."""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Float, JSON, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from db import Base


class PersonalProfile(Base):
    """Personal profile model storing user's story and preferences."""
    __tablename__ = "personal_profiles"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False, unique=True)

    # Personal information
    preferred_name = Column(String(100), nullable=True)
    avatar_id = Column(String(100), nullable=True)

    # Personal story fields
    current_situation = Column(Text, nullable=True)
    interests = Column(JSON, nullable=True, default=list)
    challenges = Column(JSON, nullable=True, default=list)
    aspirations = Column(JSON, nullable=True, default=list)
    motivation = Column(Text, nullable=True)

    # Preference learning fields
    work_style = Column(String(50), nullable=True)
    communication_frequency = Column(String(50), nullable=True)
    goal_approach = Column(String(50), nullable=True)
    motivation_style = Column(String(50), nullable=True)
    
    # Quick preferences and custom answers
    preferences = Column(JSON, nullable=True, default=dict)
    custom_answers = Column(JSON, nullable=True, default=dict)
    
    # Selected standard life areas
    selected_life_areas = Column(JSON, nullable=True, default=list)

    # AI analysis results
    story_analysis = Column(JSON, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="personal_profile")


class CustomLifeArea(Base):
    """Custom life area model for user-created categories."""
    __tablename__ = "custom_life_areas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)

    # Core fields
    name = Column(String(100), nullable=False)
    icon = Column(String(50), nullable=False, default="category")
    color = Column(String(7), nullable=False, default="#6366f1")
    description = Column(Text, nullable=True)
    keywords = Column(JSON, nullable=True, default=list)

    # Organization
    priority_order = Column(Integer, nullable=False, default=0)
    is_custom = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="custom_life_areas")


class OnboardingAnalytics(Base):
    """Onboarding analytics model for tracking user behavior."""
    __tablename__ = "onboarding_analytics"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)

    # Session tracking
    session_id = Column(String, nullable=False)

    # Event details
    event_type = Column(String(50), nullable=False)
    step_name = Column(String(50), nullable=True)
    step_number = Column(Integer, nullable=True)

    # Performance metrics
    time_spent_seconds = Column(Integer, nullable=True)
    completion_percentage = Column(Float, nullable=True)

    # Additional data
    event_metadata = Column(JSON, nullable=True)

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="onboarding_analytics")


class AssistantProfile(Base):
    """
    AI Assistant Personality Profiles for personalized conversations.
    Each user can have multiple assistant profiles with different personalities.
    """
    __tablename__ = "assistant_profiles"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    
    # Basic profile information
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    avatar_url = Column(String, nullable=True)
    
    # AI model and language settings
    ai_model = Column(String, nullable=False, default="gpt-3.5-turbo")
    language = Column(String, nullable=False, default="en")
    
    # Behavior settings
    requires_confirmation = Column(Boolean, nullable=False, default=True)
    is_default = Column(Boolean, nullable=False, default=False)
    
    # Personality style (0-100 scale for each trait)
    style = Column(JSON, nullable=False, default=lambda: {
        "formality": 50,      # 0 = very formal, 100 = extremely casual
        "directness": 50,     # 0 = very indirect, 100 = extremely direct
        "humor": 30,          # 0 = serious, 100 = humorous
        "empathy": 70,        # 0 = cold, 100 = warm and emotional
        "motivation": 60      # 0 = passive, 100 = high-energy motivator
    })
    
    # Temperature settings for different use cases
    dialogue_temperature = Column(Float, nullable=False, default=0.8)
    intent_temperature = Column(Float, nullable=False, default=0.3)
    
    # Additional configuration
    custom_instructions = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="assistant_profiles")


class OnboardingState(Base):
    """
    Tracks user's progress through the onboarding flow.
    Stores current step, completed steps, and collected data.
    """
    __tablename__ = "onboarding_states"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.uid"), unique=True, nullable=False)
    
    # Onboarding progress tracking
    current_step = Column(Integer, nullable=False, default=1)  # Current step number (1-6)
    completed_steps = Column(JSON, nullable=False, default=list)  # List of completed step numbers
    onboarding_completed = Column(Boolean, nullable=False, default=False)
    
    # Data collected during onboarding
    assistant_profile_id = Column(String, ForeignKey("assistant_profiles.id"), nullable=True)
    selected_life_areas = Column(JSON, nullable=False, default=list)  # Life area IDs selected
    first_goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    first_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    # Temporary data during onboarding
    temp_data = Column(JSON, nullable=False, default=dict)  # Temporary storage for incomplete steps
    
    # Onboarding preferences
    skip_intro = Column(Boolean, nullable=False, default=False)
    theme_preference = Column(String, nullable=True)  # light, dark, auto
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="onboarding_state")
    assistant_profile = relationship("AssistantProfile")
    first_goal = relationship("Goal", foreign_keys=[first_goal_id])
    first_task = relationship("Task", foreign_keys=[first_task_id])


# Performance indexes for PersonalProfile model
Index('ix_personal_profiles_user_id', PersonalProfile.user_id)

# Performance indexes for CustomLifeArea model
Index('ix_custom_life_areas_user_id', CustomLifeArea.user_id)
Index('ix_custom_life_areas_priority', CustomLifeArea.user_id, CustomLifeArea.priority_order)

# Performance indexes for OnboardingAnalytics model
Index('ix_onboarding_analytics_user_id', OnboardingAnalytics.user_id)
Index('ix_onboarding_analytics_event', OnboardingAnalytics.event_type, OnboardingAnalytics.created_at.desc())

# Performance indexes for AssistantProfile model
Index('ix_assistant_profiles_user_default', AssistantProfile.user_id, AssistantProfile.is_default)
Index('ix_assistant_profiles_user_created', AssistantProfile.user_id, AssistantProfile.created_at.desc())

# Performance indexes for OnboardingState model
Index('ix_onboarding_state_user', OnboardingState.user_id)
Index('ix_onboarding_state_completed', OnboardingState.onboarding_completed, OnboardingState.completed_at.desc())
Index('ix_onboarding_state_activity', OnboardingState.last_activity.desc())