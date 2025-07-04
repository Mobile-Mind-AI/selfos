"""Conversation and AI interaction models."""

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Float, JSON, Boolean, Index, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from uuid import uuid4
from db import Base


class ConversationLog(Base):
    """
    Stores detailed conversation logs for AI interactions.
    Used for debugging, analytics, and model improvement.
    """
    __tablename__ = "conversation_logs"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    session_id = Column(String, ForeignKey("conversation_sessions.id"), nullable=False)
    
    # Conversation details
    conversation_turn = Column(Integer, nullable=False)  # Turn number in conversation
    user_message = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    
    # AI processing metadata
    intent = Column(String, nullable=True)  # Detected user intent
    confidence = Column(Float, nullable=True)  # Intent detection confidence (0.0-1.0)
    entities = Column(JSON, nullable=True)  # Extracted entities from user message
    context = Column(JSON, nullable=True)  # Context used for response generation
    
    # Model information
    model_used = Column(String, nullable=False)  # AI model used for response
    temperature = Column(Float, nullable=True)  # Temperature setting used
    max_tokens = Column(Integer, nullable=True)  # Max tokens setting used
    
    # Performance metrics
    response_time_ms = Column(Integer, nullable=True)  # Time to generate response
    token_count_input = Column(Integer, nullable=True)  # Input token count
    token_count_output = Column(Integer, nullable=True)  # Output token count
    
    # Quality indicators
    fallback_used = Column(Boolean, default=False)  # Whether fallback response was used
    error_occurred = Column(Boolean, default=False)  # Whether an error occurred
    error_details = Column(Text, nullable=True)  # Error details if applicable
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="conversation_logs")
    session = relationship("ConversationSession", back_populates="conversation_logs")


class ConversationSession(Base):
    """
    Groups related conversation exchanges into sessions.
    Tracks session-level metadata and state.
    """
    __tablename__ = "conversation_sessions"
    
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid4()))
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    
    # Session metadata
    session_type = Column(String, nullable=False, default="general")  # general, onboarding, goal_setting, etc.
    title = Column(String, nullable=True)  # User-defined or auto-generated session title
    
    # Session state
    status = Column(String, nullable=False, default="active")  # active, paused, completed, archived
    total_turns = Column(Integer, nullable=False, default=0)
    
    # Context tracking
    current_context = Column(JSON, nullable=True)  # Current conversation context
    persistent_context = Column(JSON, nullable=True)  # Context that persists across turns
    
    # Session outcomes
    goals_created = Column(JSON, nullable=True)  # List of goal IDs created during session
    tasks_created = Column(JSON, nullable=True)  # List of task IDs created during session
    actions_taken = Column(JSON, nullable=True)  # List of actions taken during session
    
    # Quality metrics
    user_satisfaction = Column(Float, nullable=True)  # User satisfaction rating (1.0-5.0)
    session_rating = Column(Integer, nullable=True)  # Overall session rating (1-5)
    completion_percentage = Column(Float, nullable=True)  # How much of intended goal was completed
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="conversation_sessions")
    conversation_logs = relationship("ConversationLog", back_populates="session", cascade="all, delete-orphan")


class IntentFeedback(Base):
    """
    Stores user feedback on intent detection accuracy.
    Used for improving AI intent recognition.
    """
    __tablename__ = "intent_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    conversation_log_id = Column(String, ForeignKey("conversation_logs.id"), nullable=False)
    
    # Original intent detection
    original_intent = Column(String, nullable=False)  # Original detected intent
    original_confidence = Column(Float, nullable=False)  # Original confidence score
    
    # User feedback
    feedback_type = Column(Enum("correct", "incorrect", "partially_correct", name="intent_feedback_type"), nullable=False)
    correct_intent = Column(String, nullable=True)  # What the intent should have been
    feedback_quality = Column(Integer, nullable=True)  # Quality rating (1-5)
    
    # Additional context
    user_comment = Column(Text, nullable=True)  # User's explanation of the feedback
    feedback_context = Column(JSON, nullable=True)  # Additional context data
    
    # Processing status
    processed = Column(Boolean, default=False)  # Whether feedback has been processed for training
    processed_at = Column(DateTime, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="intent_feedback")
    conversation_log = relationship("ConversationLog")


# Performance indexes for ConversationLog model
Index('ix_conversation_logs_user_created', ConversationLog.user_id, ConversationLog.created_at.desc())
Index('ix_conversation_logs_session_turn', ConversationLog.session_id, ConversationLog.conversation_turn)
Index('ix_conversation_logs_intent_confidence', ConversationLog.intent, ConversationLog.confidence.desc())
Index('ix_conversation_logs_fallback', ConversationLog.fallback_used, ConversationLog.created_at.desc())

# Performance indexes for ConversationSession model
Index('ix_conversation_sessions_user_activity', ConversationSession.user_id, ConversationSession.last_activity.desc())
Index('ix_conversation_sessions_status_created', ConversationSession.status, ConversationSession.started_at.desc())
Index('ix_conversation_sessions_type_user', ConversationSession.session_type, ConversationSession.user_id)

# Performance indexes for IntentFeedback model
Index('ix_intent_feedback_user_created', IntentFeedback.user_id, IntentFeedback.created_at.desc())
Index('ix_intent_feedback_original_intent', IntentFeedback.original_intent, IntentFeedback.feedback_type)
Index('ix_intent_feedback_quality', IntentFeedback.feedback_quality, IntentFeedback.created_at.desc())