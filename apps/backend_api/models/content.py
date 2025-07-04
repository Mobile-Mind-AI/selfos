"""Content-related models: Media, Memory, Story, and Feedback."""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Float, JSON, Boolean, Index, LargeBinary, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from db import Base


class MediaAttachment(Base):
    __tablename__ = "media_attachments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    
    # Content association - one of these will be set
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    
    # Media details
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)  # MIME type
    file_size = Column(Integer, nullable=False)    # Size in bytes
    file_path = Column(String, nullable=False)     # Path to stored file
    
    # Media metadata
    media_type = Column(String, nullable=False)    # image, video, audio, document
    width = Column(Integer, nullable=True)         # For images/videos
    height = Column(Integer, nullable=True)        # For images/videos
    duration = Column(Float, nullable=True)        # For videos/audio (seconds)
    
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
    
    # Memory content
    content = Column(Text, nullable=False)
    content_type = Column(String, nullable=False, default="conversation")  # conversation, reflection, achievement
    
    # Memory metadata
    importance = Column(Float, nullable=False, default=0.5)  # 0.0 to 1.0
    context = Column(JSON, nullable=True)  # Additional context data
    
    # AI processing fields
    embedding = Column(JSON, nullable=True)  # Vector embedding for similarity search
    summary = Column(Text, nullable=True)    # AI-generated summary
    tags = Column(JSON, nullable=True)       # Extracted tags/keywords
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="memory_items")


class StorySession(Base):
    __tablename__ = "story_sessions"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    
    # Content information
    title = Column(String, nullable=True)  # User-defined title for the story session
    generated_text = Column(Text, nullable=True)  # AI-generated narrative text
    video_url = Column(String, nullable=True)  # URL to generated video
    audio_url = Column(String, nullable=True)  # URL to generated audio/narration
    thumbnail_url = Column(String, nullable=True)  # URL to video thumbnail
    
    # Content metadata
    content_type = Column(String, nullable=False, default="weekly_summary")  # weekly_summary, achievement, reflection
    word_count = Column(Integer, nullable=True)
    estimated_read_time = Column(Integer, nullable=True)  # In seconds
    
    # Generation settings used
    story_style = Column(String, nullable=True)  # narrative, journal, social_post
    target_length = Column(String, nullable=True)  # short, medium, long
    include_media = Column(Boolean, nullable=False, default=False)
    
    # Processing status
    generation_status = Column(String, nullable=False, default="pending")  # pending, processing, completed, failed
    processing_time = Column(Float, nullable=True)  # Time taken to generate (seconds)
    error_message = Column(Text, nullable=True)  # Error details if generation failed
    
    # Time period covered by this story
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    
    # Engagement metrics
    view_count = Column(Integer, nullable=False, default=0)
    like_count = Column(Integer, nullable=False, default=0)
    share_count = Column(Integer, nullable=False, default=0)
    
    # Social media posting
    posted_to_platforms = Column(JSON, nullable=True)  # List of platforms posted to
    posted_at = Column(DateTime, nullable=True)
    social_post_ids = Column(JSON, nullable=True)  # Platform-specific post IDs
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="story_sessions")


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


# Performance indexes for MediaAttachment model
Index('ix_media_user_created', MediaAttachment.user_id, MediaAttachment.created_at.desc())
Index('ix_media_user_type', MediaAttachment.user_id, MediaAttachment.media_type)
Index('ix_media_goal', MediaAttachment.goal_id, MediaAttachment.created_at.desc())
Index('ix_media_project', MediaAttachment.project_id, MediaAttachment.created_at.desc())
Index('ix_media_task', MediaAttachment.task_id, MediaAttachment.created_at.desc())

# Performance indexes for MemoryItem model
Index('ix_memory_user_timestamp', MemoryItem.user_id, MemoryItem.timestamp.desc())

# Performance indexes for StorySession model
Index('ix_story_user_created', StorySession.user_id, StorySession.created_at.desc())
Index('ix_story_user_status', StorySession.user_id, StorySession.generation_status)
Index('ix_story_user_period', StorySession.user_id, StorySession.period_start, StorySession.period_end)
Index('ix_story_content_type', StorySession.content_type, StorySession.created_at.desc())
Index('ix_story_posted_at', StorySession.posted_at)

# Performance indexes for FeedbackLog model
Index('ix_feedback_user_created', FeedbackLog.user_id, FeedbackLog.created_at.desc())
Index('ix_feedback_user_type', FeedbackLog.user_id, FeedbackLog.feedback_type)
Index('ix_feedback_context', FeedbackLog.context_type, FeedbackLog.created_at.desc())
Index('ix_feedback_session', FeedbackLog.session_id, FeedbackLog.created_at.desc())
Index('ix_feedback_processed', FeedbackLog.processed_at)  # For archival queries