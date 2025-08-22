"""
Pydantic schemas for intent classification and conversation management.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, validator


class IntentType(str, Enum):
    """Supported intent types."""

    CREATE_GOAL = "create_goal"
    CREATE_TASK = "create_task"
    CREATE_PROJECT = "create_project"
    UPDATE_SETTINGS = "update_settings"
    RATE_LIFE_AREA = "rate_life_area"
    CHAT_CONTINUATION = "chat_continuation"
    GET_ADVICE = "get_advice"
    UNKNOWN = "unknown"


class EntityType(str, Enum):
    """Supported entity types."""

    TITLE = "title"
    DUE_DATE = "due_date"
    LIFE_AREA = "life_area"
    PRIORITY = "priority"
    DURATION = "duration"
    DESCRIPTION = "description"
    SETTINGS = "settings"


class LifeAreaType(str, Enum):
    """Standard life area categories."""

    HEALTH = "Health"
    CAREER = "Career"
    RELATIONSHIPS = "Relationships"
    FINANCE = "Finance"
    PERSONAL = "Personal"
    EDUCATION = "Education"
    RECREATION = "Recreation"
    SPIRITUAL = "Spiritual"


class PriorityLevel(str, Enum):
    """Priority levels for tasks and goals."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Request/Response Schemas


class ConversationMessageRequest(BaseModel):
    """Request schema for processing a conversation message."""

    message: str = Field(
        ..., min_length=1, max_length=1000, description="User's message"
    )
    session_id: str | None = Field(None, description="Conversation session ID")
    assistant_id: str | None = Field(
        None, description="Specific assistant profile ID (uses default if not provided)"
    )
    include_context: bool = Field(
        True, description="Include user context in classification"
    )

    @validator("message")
    def validate_message(cls, v):
        if not v.strip():
            raise ValueError("Message cannot be empty or whitespace only")
        return v.strip()


class EntityExtraction(BaseModel):
    """Extracted entity with metadata."""

    type: EntityType
    value: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    source: str = Field(..., description="Source of extraction (llm, rule_based)")


class IntentClassificationResult(BaseModel):
    """Result of intent classification."""

    intent: IntentType
    confidence: float = Field(..., ge=0.0, le=1.0)
    entities: dict[str, Any] = Field(default_factory=dict)
    reasoning: str | None = None
    fallback_used: bool = False
    processing_time_ms: float


class NextAction(BaseModel):
    """Recommended next action based on intent classification."""

    type: str = Field(
        ..., description="Action type (execute_action, clarification_request, etc.)"
    )
    message: str | None = None
    required_entity: str | None = None
    action: str | None = None
    entities: dict[str, Any] | None = None
    context: dict[str, Any] | None = None
    suggested_intents: list[str] | None = None


class ConversationState(BaseModel):
    """Current state of conversation session."""

    current_intent: str | None = None
    incomplete_entities: list[str] = Field(default_factory=list)
    turn_count: int = 0
    last_update: datetime
    session_type: str = "chat"
    status: str = "active"


class ConversationMessageResponse(BaseModel):
    """Response from conversation message processing."""

    intent_result: IntentClassificationResult
    conversation_state: ConversationState
    next_actions: list[NextAction]
    requires_clarification: bool
    session_id: str


# Entity-specific schemas


class TaskEntitySet(BaseModel):
    """Entities required/optional for task creation."""

    title: str = Field(..., min_length=1, max_length=200)
    due_date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    life_area: LifeAreaType | None = None
    priority: PriorityLevel | None = PriorityLevel.MEDIUM
    duration: str | None = None
    description: str | None = Field(None, max_length=1000)


class GoalEntitySet(BaseModel):
    """Entities required/optional for goal creation."""

    title: str = Field(..., min_length=1, max_length=200)
    life_area: LifeAreaType | None = None
    description: str | None = Field(None, max_length=1000)
    target_date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")


class ProjectEntitySet(BaseModel):
    """Entities required/optional for project creation."""

    title: str = Field(..., min_length=1, max_length=200)
    life_area: LifeAreaType | None = None
    description: str | None = Field(None, max_length=1000)
    start_date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    target_date: str | None = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    priority: PriorityLevel | None = PriorityLevel.MEDIUM


class SettingsEntitySet(BaseModel):
    """Entities for settings updates."""

    setting_type: str = Field(..., description="Type of setting to update")
    setting_value: str = Field(..., description="New setting value")
    preference_category: str | None = None


class LifeAreaRatingEntitySet(BaseModel):
    """Entities for life area rating."""

    life_area: LifeAreaType
    rating: int = Field(..., ge=1, le=10, description="Rating from 1-10")
    comment: str | None = Field(None, max_length=500)


# Database model schemas


class ConversationLogCreate(BaseModel):
    """Schema for creating conversation log entries."""

    user_message: str
    intent: str
    confidence: float
    entities: dict[str, Any] = Field(default_factory=dict)
    reasoning: str | None = None
    fallback_used: bool = False
    processing_time_ms: float | None = None
    session_id: str | None = None
    conversation_turn: int = 1
    previous_intent: str | None = None
    user_context: dict[str, Any] | None = None


class ConversationLogOut(BaseModel):
    """Schema for conversation log output."""

    id: int
    user_id: str
    session_id: str | None
    user_message: str
    intent: str
    confidence: float
    entities: dict[str, Any]
    reasoning: str | None
    fallback_used: bool
    processing_time_ms: float | None
    conversation_turn: int
    previous_intent: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationSessionCreate(BaseModel):
    """Schema for creating conversation sessions."""

    session_type: str = "chat"
    current_intent: str | None = None
    incomplete_entities: dict[str, Any] = Field(default_factory=dict)
    context_data: dict[str, Any] = Field(default_factory=dict)


class ConversationSessionOut(BaseModel):
    """Schema for conversation session output."""

    id: str
    user_id: str
    session_type: str
    status: str
    current_intent: str | None
    incomplete_entities: dict[str, Any]
    context_data: dict[str, Any]
    turn_count: int
    successful_intents: int
    failed_intents: int
    avg_confidence: float | None
    started_at: datetime
    last_activity: datetime
    completed_at: datetime | None

    class Config:
        from_attributes = True


class IntentFeedbackCreate(BaseModel):
    """Schema for creating intent feedback."""

    conversation_log_id: int
    original_intent: str
    original_confidence: float
    original_entities: dict[str, Any] = Field(default_factory=dict)
    corrected_intent: str
    corrected_entities: dict[str, Any] = Field(default_factory=dict)
    feedback_type: str = Field(
        ..., pattern=r"^(wrong_intent|missing_entity|wrong_entity)$"
    )
    user_comment: str | None = Field(None, max_length=1000)

    @validator("corrected_intent")
    def validate_corrected_intent(cls, v):
        valid_intents = [intent.value for intent in IntentType]
        if v not in valid_intents:
            raise ValueError(f"Invalid intent. Must be one of: {valid_intents}")
        return v


class IntentFeedbackOut(BaseModel):
    """Schema for intent feedback output."""

    id: int
    user_id: str
    conversation_log_id: int
    original_intent: str
    original_confidence: float
    original_entities: dict[str, Any]
    corrected_intent: str
    corrected_entities: dict[str, Any]
    feedback_type: str
    user_comment: str | None
    feedback_quality: str | None
    created_at: datetime

    class Config:
        from_attributes = True


# Analytics and reporting schemas


class IntentAnalytics(BaseModel):
    """Analytics data for intent classification performance."""

    total_messages: int
    intent_distribution: dict[str, int]
    avg_confidence: float
    fallback_usage_rate: float
    avg_processing_time_ms: float
    success_rate: float
    common_failure_patterns: list[dict[str, Any]]


class ConversationAnalytics(BaseModel):
    """Analytics data for conversation sessions."""

    total_sessions: int
    avg_session_length: float
    completion_rate: float
    avg_turns_per_session: float
    intent_success_rate: float
    most_common_intents: list[dict[str, Any]]
    user_satisfaction_score: float | None


class EntityExtractionAccuracy(BaseModel):
    """Analytics for entity extraction accuracy."""

    entity_type: str
    total_extractions: int
    correct_extractions: int
    accuracy_rate: float
    common_errors: list[dict[str, Any]]
    extraction_sources: dict[str, int]  # llm vs rule_based


# Configuration schemas


class IntentClassifierConfig(BaseModel):
    """Configuration for intent classifier."""

    confidence_threshold: float = Field(0.85, ge=0.0, le=1.0)
    enable_fallback: bool = True
    enable_logging: bool = True
    max_entities_per_message: int = 10
    session_timeout_minutes: int = 30
    llm_temperature: float = Field(0.1, ge=0.0, le=1.0)
    llm_max_tokens: int = Field(500, ge=100, le=2000)


class ConversationFlowConfig(BaseModel):
    """Configuration for conversation flow management."""

    max_clarification_attempts: int = 3
    entity_collection_timeout_minutes: int = 5
    auto_complete_sessions: bool = True
    enable_proactive_suggestions: bool = True
    context_window_messages: int = 10
