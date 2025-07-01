from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Float, JSON, Boolean, Enum, Time, func, Index
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
    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    life_areas = relationship("LifeArea", back_populates="user", cascade="all, delete-orphan")
    media_attachments = relationship("MediaAttachment", back_populates="user", cascade="all, delete-orphan")
    memory_items = relationship("MemoryItem", back_populates="user", cascade="all, delete-orphan")
    preferences = relationship("UserPreferences", back_populates="user", cascade="all, delete-orphan", uselist=False)
    feedback_logs = relationship("FeedbackLog", back_populates="user", cascade="all, delete-orphan")
    story_sessions = relationship("StorySession", back_populates="user", cascade="all, delete-orphan")

class Goal(Base):
    __tablename__ = "goals"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    life_area_id = Column(Integer, ForeignKey("life_areas.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
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
    project = relationship("Project", back_populates="goals")
    tasks = relationship("Task", back_populates="goal", cascade="all, delete-orphan")
    media_attachments = relationship("MediaAttachment", back_populates="goal")

# Performance indexes for Goal model
Index('ix_goals_user_created', Goal.user_id, Goal.created_at.desc())
Index('ix_goals_user_status', Goal.user_id, Goal.status)
Index('ix_goals_life_area_created', Goal.life_area_id, Goal.created_at.desc())
Index('ix_goals_project_created', Goal.project_id, Goal.created_at.desc())

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    life_area_id = Column(Integer, ForeignKey("life_areas.id"), nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    # Status: e.g., todo, in_progress, completed, paused
    status = Column(String, nullable=False, default='todo')
    # Progress percentage 0.0 - 100.0
    progress = Column(Float, nullable=False, default=0.0)
    # Optional start and end dates for the project
    start_date = Column(DateTime)
    target_date = Column(DateTime)
    # Project priority: low, medium, high
    priority = Column(String, nullable=False, default='medium')
    # Project phases/milestones as JSON
    phases = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="projects")
    life_area = relationship("LifeArea", back_populates="projects")
    goals = relationship("Goal", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project")
    media_attachments = relationship("MediaAttachment", back_populates="project")

# Performance indexes for Project model
Index('ix_projects_user_created', Project.user_id, Project.created_at.desc())
Index('ix_projects_user_status', Project.user_id, Project.status)
Index('ix_projects_life_area_created', Project.life_area_id, Project.created_at.desc())
Index('ix_projects_user_priority', Project.user_id, Project.priority)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
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
    project = relationship("Project", back_populates="tasks")
    life_area = relationship("LifeArea", back_populates="tasks")
    media_attachments = relationship("MediaAttachment", back_populates="task")

# Performance indexes for Task model
Index('ix_tasks_user_created', Task.user_id, Task.created_at.desc())
Index('ix_tasks_user_status', Task.user_id, Task.status)
Index('ix_tasks_goal_created', Task.goal_id, Task.created_at.desc())
Index('ix_tasks_project_created', Task.project_id, Task.created_at.desc())
Index('ix_tasks_due_date', Task.user_id, Task.due_date)
# Partial index for completed tasks (PostgreSQL specific, will be in migration)
Index('ix_tasks_completed', Task.user_id, Task.created_at.desc(), postgresql_where=(Task.status == 'completed'))

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
    projects = relationship("Project", back_populates="life_area")
    tasks = relationship("Task", back_populates="life_area")

# Performance indexes for LifeArea model
Index('ix_life_areas_user_created', LifeArea.user_id, LifeArea.created_at.desc())
Index('ix_life_areas_user_name', LifeArea.user_id, LifeArea.name)

class MediaAttachment(Base):
    __tablename__ = "media_attachments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    # What this attachment is linked to
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
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
    project = relationship("Project", back_populates="media_attachments")
    task = relationship("Task", back_populates="media_attachments")

# Performance indexes for MediaAttachment model
Index('ix_media_user_created', MediaAttachment.user_id, MediaAttachment.created_at.desc())
Index('ix_media_user_type', MediaAttachment.user_id, MediaAttachment.file_type)
Index('ix_media_goal', MediaAttachment.goal_id, MediaAttachment.created_at.desc())
Index('ix_media_project', MediaAttachment.project_id, MediaAttachment.created_at.desc())
Index('ix_media_task', MediaAttachment.task_id, MediaAttachment.created_at.desc())

class MemoryItem(Base):
    __tablename__ = "memory_items"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="memory_items")

# Performance indexes for MemoryItem model
Index('ix_memory_user_timestamp', MemoryItem.user_id, MemoryItem.timestamp.desc())

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
    
    # Generation parameters
    summary_period = Column(String, nullable=True)  # "weekly", "monthly", "project-based", "custom", etc.
    period_start = Column(DateTime, nullable=True)  # Start of the period being summarized
    period_end = Column(DateTime, nullable=True)  # End of the period being summarized
    content_type = Column(Enum("summary", "story", "reflection", "achievement", name="story_content_type"), default="summary")
    
    # Social media and distribution
    posted_to = Column(JSON, nullable=True, default=list)  # e.g., ["instagram", "youtube", "twitter"]
    posting_status = Column(Enum("draft", "scheduled", "posted", "failed", name="posting_status"), default="draft")
    scheduled_post_time = Column(DateTime, nullable=True)  # When content is scheduled to be posted
    
    # Generation metadata
    generation_prompt = Column(Text, nullable=True)  # The prompt used for generation
    model_version = Column(String, nullable=True)  # AI model version used
    generation_params = Column(JSON, nullable=True)  # Parameters used for generation (temperature, etc.)
    word_count = Column(Integer, nullable=True)  # Word count of generated text
    estimated_read_time = Column(Integer, nullable=True)  # Estimated reading time in seconds
    
    # Related content
    source_goals = Column(JSON, nullable=True, default=list)  # Goal IDs that contributed to this story
    source_tasks = Column(JSON, nullable=True, default=list)  # Task IDs that contributed to this story
    source_life_areas = Column(JSON, nullable=True, default=list)  # Life area IDs featured in this story
    
    # Engagement and analytics
    view_count = Column(Integer, default=0)  # Number of times viewed
    like_count = Column(Integer, default=0)  # Number of likes (if posted)
    share_count = Column(Integer, default=0)  # Number of shares
    engagement_data = Column(JSON, nullable=True)  # Additional engagement metrics
    
    # Quality and user feedback
    user_rating = Column(Float, nullable=True)  # User rating 1-5 stars
    user_notes = Column(Text, nullable=True)  # User notes about the story
    regeneration_count = Column(Integer, default=0)  # How many times this was regenerated
    
    # Processing status
    processing_status = Column(Enum("pending", "generating", "completed", "failed", name="processing_status"), default="pending")
    error_message = Column(Text, nullable=True)  # Error message if generation failed
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    generated_at = Column(DateTime, nullable=True)  # When generation was completed
    posted_at = Column(DateTime, nullable=True)  # When content was actually posted
    
    # Relationships
    user = relationship("User", back_populates="story_sessions")

# Performance indexes for StorySession model
Index('ix_story_user_created', StorySession.user_id, StorySession.created_at.desc())
Index('ix_story_user_status', StorySession.user_id, StorySession.processing_status)
Index('ix_story_user_period', StorySession.user_id, StorySession.summary_period)
Index('ix_story_posted_at', StorySession.posted_at)  # For archival queries
Index('ix_story_content_type', StorySession.content_type, StorySession.created_at.desc())


class ConversationLog(Base):
    """
    Log of conversation interactions for intent classification debugging and tuning.
    Stores user inputs, detected intents, confidence scores, and extracted entities.
    """
    __tablename__ = "conversation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    session_id = Column(String, nullable=True)  # For grouping related messages
    
    # Input and classification results
    user_message = Column(Text, nullable=False)
    intent = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    entities = Column(JSON, nullable=False, default=dict)
    
    # Classification metadata
    reasoning = Column(Text, nullable=True)
    fallback_used = Column(Boolean, nullable=False, default=False)
    processing_time_ms = Column(Float, nullable=True)
    
    # Conversation context
    conversation_turn = Column(Integer, nullable=False, default=1)
    previous_intent = Column(String, nullable=True)
    user_context = Column(JSON, nullable=True)  # User state at time of message
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="conversation_logs")


class ConversationSession(Base):
    """
    Conversation session tracking for multi-turn interactions.
    Groups related messages and tracks conversation state.
    """
    __tablename__ = "conversation_sessions"
    
    id = Column(String, primary_key=True, index=True)  # UUID
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    
    # Session metadata
    session_type = Column(String, nullable=False, default='chat')  # chat, onboarding, support
    status = Column(String, nullable=False, default='active')  # active, completed, abandoned
    
    # Conversation state
    current_intent = Column(String, nullable=True)
    incomplete_entities = Column(JSON, nullable=False, default=dict)
    context_data = Column(JSON, nullable=False, default=dict)
    
    # Session metrics
    turn_count = Column(Integer, nullable=False, default=0)
    successful_intents = Column(Integer, nullable=False, default=0)
    failed_intents = Column(Integer, nullable=False, default=0)
    avg_confidence = Column(Float, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="conversation_sessions")


class IntentFeedback(Base):
    """
    User feedback on intent classification accuracy for model improvement.
    Allows users to correct misclassified intents.
    """
    __tablename__ = "intent_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.uid"), nullable=False)
    conversation_log_id = Column(Integer, ForeignKey("conversation_logs.id"), nullable=False)
    
    # Original classification
    original_intent = Column(String, nullable=False)
    original_confidence = Column(Float, nullable=False)
    original_entities = Column(JSON, nullable=False, default=dict)
    
    # User corrections
    corrected_intent = Column(String, nullable=False)
    corrected_entities = Column(JSON, nullable=False, default=dict)
    feedback_type = Column(String, nullable=False)  # wrong_intent, missing_entity, wrong_entity
    
    # Feedback metadata
    user_comment = Column(Text, nullable=True)
    feedback_quality = Column(String, nullable=True)  # helpful, not_helpful, spam
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="intent_feedback")
    conversation_log = relationship("ConversationLog")


# Add new relationships to User model
User.conversation_logs = relationship("ConversationLog", back_populates="user", cascade="all, delete-orphan")
User.conversation_sessions = relationship("ConversationSession", back_populates="user", cascade="all, delete-orphan")
User.intent_feedback = relationship("IntentFeedback", back_populates="user", cascade="all, delete-orphan")

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
    prompt_modifiers = Column(JSON, nullable=True, default=dict)
    custom_instructions = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="assistant_profiles")


# Add assistant_profiles relationship to User model
User.assistant_profiles = relationship("AssistantProfile", back_populates="user", cascade="all, delete-orphan")

# Performance indexes for AssistantProfile model
Index('ix_assistant_profiles_user_default', AssistantProfile.user_id, AssistantProfile.is_default)
Index('ix_assistant_profiles_user_created', AssistantProfile.user_id, AssistantProfile.created_at.desc())
Index('ix_assistant_profiles_model', AssistantProfile.ai_model)