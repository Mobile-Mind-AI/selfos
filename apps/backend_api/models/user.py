"""User-related models."""

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Time, Index, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from db import Base


class User(Base):
    __tablename__ = "users"
    uid = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    
    # Relationships - defined here but will reference models from other modules
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    life_areas = relationship("LifeArea", back_populates="user", cascade="all, delete-orphan")
    media_attachments = relationship("MediaAttachment", back_populates="user", cascade="all, delete-orphan")
    memory_items = relationship("MemoryItem", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", cascade="all, delete-orphan", uselist=False)
    feedback_logs = relationship("FeedbackLog", back_populates="user", cascade="all, delete-orphan")
    story_sessions = relationship("StorySession", back_populates="user", cascade="all, delete-orphan")
    personal_profile = relationship("PersonalProfile", back_populates="user", uselist=False)
    custom_life_areas = relationship("CustomLifeArea", back_populates="user", cascade="all, delete-orphan")
    onboarding_analytics = relationship("OnboardingAnalytics", back_populates="user", cascade="all, delete-orphan")
    assistant_profiles = relationship("AssistantProfile", back_populates="user", cascade="all, delete-orphan")
    onboarding_state = relationship("OnboardingState", back_populates="user", uselist=False)
    conversation_logs = relationship("ConversationLog", back_populates="user", cascade="all, delete-orphan")
    conversation_sessions = relationship("ConversationSession", back_populates="user", cascade="all, delete-orphan")
    intent_feedback = relationship("IntentFeedback", back_populates="user", cascade="all, delete-orphan")


class UserPreferences(Base):
    __tablename__ = "user_preferences"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.uid"), unique=True, nullable=False)
    
    # Tone and communication preferences
    tone = Column(Enum("friendly", "coach", "minimal", "professional", name="tone_style"), default="friendly")
    
    # Notification preferences
    notification_time = Column(Time)  # Preferred time for daily notifications
    notifications_enabled = Column(Boolean, default=True)
    email_notifications = Column(Boolean, default=False)
    
    # Content and visualization preferences
    prefers_video = Column(Boolean, default=True)
    prefers_audio = Column(Boolean, default=False)
    default_view = Column(Enum("list", "card", "timeline", name="view_mode"), default="card")
    
    # Feature preferences
    mood_tracking_enabled = Column(Boolean, default=False)
    progress_charts_enabled = Column(Boolean, default=True)
    ai_suggestions_enabled = Column(Boolean, default=True)
    
    # Default associations
    default_life_area_id = Column(Integer, ForeignKey("life_areas.id"), nullable=True)
    
    # Privacy and data preferences
    data_sharing_enabled = Column(Boolean, default=False)
    analytics_enabled = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="preferences")
    default_life_area = relationship("LifeArea", foreign_keys=[default_life_area_id])


# Performance indexes for UserPreferences model  
Index('ix_user_prefs_user_created', UserPreferences.user_id, UserPreferences.created_at.desc())