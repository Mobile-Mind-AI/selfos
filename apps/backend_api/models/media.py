"""
MediaAttachment model for SelfOS Backend API.
"""

from datetime import datetime

from sqlalchemy import (
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


class MediaAttachment(Base):
    __tablename__ = "media_attachments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)

    # Media category - unified for all media types
    category = Column(
        String, nullable=False, default="attachment"
    )  # "attachment", "avatar", "cover", "generated"

    # What this attachment is linked to
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)

    # File information
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    mime_type = Column(
        String, nullable=False
    )  # e.g., image/jpeg, video/mp4, audio/mpeg
    file_type = Column(String, nullable=False)  # image, video, audio, document

    # Avatar-specific fields (only used when category="avatar")
    is_active_avatar = Column(Boolean, nullable=False, default=False)
    avatar_type = Column(String, nullable=True)  # "custom", "preset", "generated"

    # Optional metadata
    title = Column(String)  # User-defined title
    description = Column(Text)  # User description for storytelling
    duration = Column(Integer)  # Duration in seconds for video/audio
    width = Column(Integer)  # Image/video width
    height = Column(Integer)  # Image/video height

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)  # For tracking avatar usage

    # Relationships
    user = relationship("User", back_populates="media_attachments")
    goal = relationship("Goal", back_populates="media_attachments")
    project = relationship("Project", back_populates="media_attachments")
    task = relationship("Task", back_populates="media_attachments")


# Performance indexes for MediaAttachment model
Index(
    "ix_media_user_created", MediaAttachment.user_id, MediaAttachment.created_at.desc()
)
Index("ix_media_user_type", MediaAttachment.user_id, MediaAttachment.file_type)
Index("ix_media_goal", MediaAttachment.goal_id, MediaAttachment.created_at.desc())
Index("ix_media_project", MediaAttachment.project_id, MediaAttachment.created_at.desc())
Index("ix_media_task", MediaAttachment.task_id, MediaAttachment.created_at.desc())
Index("ix_media_user_category", MediaAttachment.user_id, MediaAttachment.category)
Index("ix_media_user_avatar", MediaAttachment.user_id, MediaAttachment.is_active_avatar)
