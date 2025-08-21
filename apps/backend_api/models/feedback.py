"""
FeedbackLog model for SelfOS Backend API.
"""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Float, JSON, Enum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from .base import Base


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

# Performance indexes for FeedbackLog model
Index('ix_feedback_user_created', FeedbackLog.user_id, FeedbackLog.created_at.desc())
Index('ix_feedback_user_type', FeedbackLog.user_id, FeedbackLog.feedback_type)
Index('ix_feedback_context', FeedbackLog.context_type, FeedbackLog.created_at.desc())
Index('ix_feedback_session', FeedbackLog.session_id, FeedbackLog.created_at.desc())
Index('ix_feedback_processed', FeedbackLog.processed_at)  # For archival queries
