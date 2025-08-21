"""
UserPreferences model for SelfOS Backend API.
"""

from sqlalchemy import Column, String, Integer, Time, DateTime, ForeignKey, Boolean, Enum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from .base import Base


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

class UserPreferencesHistory(Base):
    __tablename__ = "user_preferences_history"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.uid"), nullable=False, index=True)
    preference_name = Column(String, nullable=False)
    old_value = Column(String, nullable=True)
    new_value = Column(String, nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User", back_populates="preferences_history")

# Performance indexes for UserPreferences model  
Index('ix_user_prefs_user_created', UserPreferences.user_id, UserPreferences.created_at.desc())

# Performance indexes for UserPreferencesHistory model
Index('ix_user_prefs_history_user_time', UserPreferencesHistory.user_id, UserPreferencesHistory.changed_at.desc())
Index('ix_user_prefs_history_pref_name', UserPreferencesHistory.preference_name)
