"""
StorySession model for SelfOS Backend API.
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Float, JSON, Enum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from .base import Base


class StorySession(Base):
    __tablename__ = "story_sessions"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    
    # Story metadata
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    theme = Column(String, nullable=True)  # "productivity", "wellness", "achievement", etc.
    
    # Content and generation details
    script = Column(Text, nullable=True)  # Generated narrative script
    media_urls = Column(JSON, nullable=False, default=list)  # URLs of generated media
    music_url = Column(String, nullable=True)  # Background music URL
    
    # Story components and sources
    included_goals = Column(JSON, nullable=False, default=list)  # Goal IDs included
    included_tasks = Column(JSON, nullable=False, default=list)  # Task IDs included
    included_media = Column(JSON, nullable=False, default=list)  # MediaAttachment IDs
    
    # Generation parameters
    duration = Column(Integer, nullable=True)  # Target duration in seconds
    style = Column(String, nullable=True, default="documentary")  # "documentary", "motivational", "recap"
    voice_type = Column(String, nullable=True, default="natural")  # TTS voice selection
    
    # Status tracking
    status = Column(
        Enum("draft", "generating", "ready", "published", "archived", name="story_status"),
        nullable=False,
        default="draft"
    )
    generation_progress = Column(Float, nullable=False, default=0.0)  # 0-100
    error_message = Column(Text, nullable=True)  # If generation failed
    
    # Publishing and sharing
    is_public = Column(String, nullable=False, default="false")  # "true"/"false" as string for consistency
    share_token = Column(String, nullable=True, unique=True)  # For sharing private stories
    view_count = Column(Integer, nullable=False, default=0)
    
    # Export details
    exported_platforms = Column(JSON, nullable=False, default=list)  # ["tiktok", "instagram", etc.]
    export_urls = Column(JSON, nullable=False, default=dict)  # {"tiktok": "url", "instagram": "url"}
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    generated_at = Column(DateTime, nullable=True)  # When generation completed
    published_at = Column(DateTime, nullable=True)  # When made public
    last_viewed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="story_sessions")

# Performance indexes for StorySession model
Index('ix_story_user_created', StorySession.user_id, StorySession.created_at.desc())
Index('ix_story_user_status', StorySession.user_id, StorySession.status)
Index('ix_story_share_token', StorySession.share_token)
Index('ix_story_public_published', StorySession.is_public, StorySession.published_at.desc())
