from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Float, JSON, Boolean, Enum, Time, func
from sqlalchemy.orm import relationship
import db
Base = db.Base
from datetime import datetime
from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID

class User(Base):
    __tablename__ = "users"
    uid = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    
    # Relationships
    goals = relationship("Goal", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    life_areas = relationship("LifeArea", back_populates="user", cascade="all, delete-orphan")
    media_attachments = relationship("MediaAttachment", back_populates="user", cascade="all, delete-orphan")
    memory_items = relationship("MemoryItem", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", cascade="all, delete-orphan", uselist=False)
    feedback_logs = relationship("FeedbackLog", back_populates="user", cascade="all, delete-orphan")

class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    life_area_id = Column(Integer, ForeignKey("life_areas.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    # Status: e.g., todo, in_progress, completed
    status = Column(String, nullable=False, default='todo')
    # Progress percentage 0.0 - 100.0
    progress = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="goals")
    life_area = relationship("LifeArea", back_populates="goals")
    tasks = relationship("Task", back_populates="goal", cascade="all, delete-orphan")
    media_attachments = relationship("MediaAttachment", back_populates="goal")

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    life_area_id = Column(Integer, ForeignKey("life_areas.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    # When task is due
    due_date = Column(DateTime)
    # Expected duration in minutes
    duration = Column(Integer)
    # Status: todo, in_progress, completed
    status = Column(String, nullable=False, default='todo')
    # Progress percentage 0.0 - 100.0
    progress = Column(Float, nullable=False, default=0.0)
    # List of prerequisite task IDs (kept as JSON for simplicity)
    dependencies = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    goal = relationship("Goal", back_populates="tasks")
    life_area = relationship("LifeArea", back_populates="tasks")
    media_attachments = relationship("MediaAttachment", back_populates="task")

class LifeArea(Base):
    __tablename__ = "life_areas"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    name = Column(String, nullable=False)
    # Weight as percentage importance (0-100)
    weight = Column(Integer, default=10, nullable=False)
    # Optional UI icon identifier
    icon = Column(String)
    # UI color preference (hex color or color name)
    color = Column(String)
    # Description of this life area
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="life_areas")
    goals = relationship("Goal", back_populates="life_area")
    tasks = relationship("Task", back_populates="life_area")

class MediaAttachment(Base):
    __tablename__ = "media_attachments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    # What this attachment is linked to
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    # File information
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    mime_type = Column(String, nullable=False)  # e.g., image/jpeg, video/mp4, audio/mpeg
    file_type = Column(String, nullable=False)  # image, video, audio, document
    # Optional metadata
    title = Column(String)  # User-defined title
    description = Column(Text)  # User description for storytelling
    duration = Column(Integer)  # Duration in seconds for video/audio
    width = Column(Integer)  # Image/video width
    height = Column(Integer)  # Image/video height
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="media_attachments")
    goal = relationship("Goal", back_populates="media_attachments")
    task = relationship("Task", back_populates="media_attachments")

class MemoryItem(Base):
    __tablename__ = "memory_items"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="memory_items")

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

class FeedbackLog(Base):
    __tablename__ = "feedback_logs"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    
    # Context information for the feedback
    context_type = Column(String, nullable=False)  # "task", "goal", "plan", "suggestion", "ui_interaction", etc.
    context_id = Column(String, nullable=True)  # ID of the related entity (goal_id, task_id, etc.)
    context_data = Column(JSON, nullable=True)  # Additional context data (query, response, etc.)
    
    # Feedback details
    feedback_type = Column(Enum("positive", "negative", "neutral", name="feedback_type"), nullable=False)
    feedback_value = Column(Float, nullable=True)  # Numeric feedback score (-1.0 to 1.0)
    comment = Column(Text, nullable=True)  # Optional user comment
    
    # ML/RLHF specific fields
    action_taken = Column(JSON, nullable=True)  # What action was taken (for RL)
    reward_signal = Column(Float, nullable=True)  # Computed reward signal
    model_version = Column(String, nullable=True)  # Version of model that generated the response
    
    # Metadata
    session_id = Column(String, nullable=True)  # Session identifier for grouping related feedback
    device_info = Column(JSON, nullable=True)  # Device/platform information
    feature_flags = Column(JSON, nullable=True)  # Active feature flags during interaction
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)  # When feedback was processed for training
    
    # Relationships
    user = relationship("User", back_populates="feedback_logs")