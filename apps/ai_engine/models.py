"""
AI Engine Data Models

Data structures for AI requests, responses, and processing results.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class RequestType(Enum):
    """Types of AI requests."""

    GOAL_DECOMPOSITION = "goal_decomposition"
    TASK_GENERATION = "task_generation"
    CONVERSATION = "conversation"
    TASK_OPTIMIZATION = "task_optimization"
    PROGRESS_ANALYSIS = "progress_analysis"


class ResponseStatus(Enum):
    """Status of AI responses."""

    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"
    RATE_LIMITED = "rate_limited"
    TIMEOUT = "timeout"


@dataclass
class AIRequest:
    """Base class for AI requests."""

    request_type: RequestType
    user_id: str
    prompt: str
    context: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    max_tokens: int | None = None
    temperature: float | None = None
    timeout: int | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class GoalDecompositionRequest(AIRequest):
    """Request for goal decomposition."""

    goal_description: str = ""
    life_areas: list[dict[str, Any]] = field(default_factory=list)
    existing_goals: list[dict[str, Any]] = field(default_factory=list)
    user_preferences: dict[str, Any] | None = None
    additional_context: str | None = None

    def __post_init__(self):
        self.request_type = RequestType.GOAL_DECOMPOSITION


@dataclass
class TaskGenerationRequest(AIRequest):
    """Request for task generation."""

    goal_id: int = 0
    goal_title: str = ""
    goal_description: str | None = None
    existing_tasks: list[dict[str, Any]] = field(default_factory=list)
    completed_tasks: list[dict[str, Any]] = field(default_factory=list)
    generation_type: str = "next_tasks"  # next_tasks, optimize_sequence, break_down
    constraints: str | None = None

    def __post_init__(self):
        self.request_type = RequestType.TASK_GENERATION


@dataclass
class ConversationRequest(AIRequest):
    """Request for conversational AI."""

    message: str = ""
    conversation_history: list[dict[str, str]] = field(default_factory=list)
    user_context: dict[str, Any] | None = None
    intent: str | None = None

    def __post_init__(self):
        self.request_type = RequestType.CONVERSATION


@dataclass
class AIResponse:
    """Base class for AI responses."""

    request_id: str
    status: ResponseStatus
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    error_message: str | None = None
    token_usage: dict[str, int] | None = None
    cost_estimate: float | None = None
    processing_time: float | None = None
    model_used: str | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ParsedTask:
    """Structured representation of a task parsed from AI response."""

    title: str
    description: str
    estimated_duration: int | None = None  # in minutes
    dependencies: list[int] = field(default_factory=list)
    life_area_id: int | None = None
    timeline: str | None = None
    success_criteria: str | None = None
    priority: str | None = None
    resources_needed: list[str] = field(default_factory=list)


@dataclass
class GoalDecompositionResponse(AIResponse):
    """Response from goal decomposition."""

    suggested_tasks: list[ParsedTask] = field(default_factory=list)
    overall_timeline: str | None = None
    potential_challenges: list[str] = field(default_factory=list)
    success_metrics: list[str] = field(default_factory=list)
    next_steps: list[str] = field(default_factory=list)
    suggested_life_area: dict[str, str] | None = None
    confidence_score: float | None = None


@dataclass
class TaskGenerationResponse(AIResponse):
    """Response from task generation."""

    generated_tasks: list[ParsedTask] = field(default_factory=list)
    optimized_sequence: list[int] = field(default_factory=list)  # Task IDs in order
    parallel_opportunities: list[list[int]] = field(
        default_factory=list
    )  # Groups of parallel tasks
    critical_path: list[int] = field(default_factory=list)
    time_estimate: str | None = None
    recommendations: list[str] = field(default_factory=list)


@dataclass
class ConversationResponse(AIResponse):
    """Response from conversational AI."""

    intent_detected: str | None = None
    suggested_actions: list[dict[str, Any]] = field(default_factory=list)
    follow_up_questions: list[str] = field(default_factory=list)
    extracted_goals: list[str] = field(default_factory=list)
    sentiment: str | None = None


@dataclass
class ProcessingMetrics:
    """Metrics for AI processing performance."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_processing_time: float = 0.0
    total_tokens_used: int = 0
    total_cost: float = 0.0
    cache_hit_rate: float = 0.0
    error_rate: float = 0.0

    def add_request(self, response: AIResponse):
        """Add a completed request to metrics."""
        self.total_requests += 1

        if response.status == ResponseStatus.SUCCESS:
            self.successful_requests += 1
        else:
            self.failed_requests += 1

        if response.processing_time:
            # Update rolling average
            total_time = self.average_processing_time * (self.total_requests - 1)
            self.average_processing_time = (
                total_time + response.processing_time
            ) / self.total_requests

        if response.token_usage:
            self.total_tokens_used += sum(response.token_usage.values())

        if response.cost_estimate:
            self.total_cost += response.cost_estimate

        self.error_rate = self.failed_requests / self.total_requests


@dataclass
class CacheEntry:
    """Cache entry for AI responses."""

    key: str
    response: AIResponse
    created_at: datetime
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.utcnow)

    def is_expired(self, ttl: int) -> bool:
        """Check if cache entry is expired."""
        age = (datetime.utcnow() - self.created_at).total_seconds()
        return age > ttl

    def access(self):
        """Mark cache entry as accessed."""
        self.access_count += 1
        self.last_accessed = datetime.utcnow()


@dataclass
class TokenUsage:
    """Token usage information."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    @property
    def efficiency_ratio(self) -> float:
        """Ratio of completion to prompt tokens (higher is more efficient)."""
        return (
            self.completion_tokens / self.prompt_tokens
            if self.prompt_tokens > 0
            else 0.0
        )


class PromptTemplate:
    """Template for generating prompts with variable substitution."""

    def __init__(self, template: str, required_vars: list[str] = None):
        self.template = template
        self.required_vars = required_vars or []

    def render(self, **kwargs) -> str:
        """Render template with provided variables."""
        # Check required variables
        missing_vars = [var for var in self.required_vars if var not in kwargs]
        if missing_vars:
            raise ValueError(f"Missing required variables: {missing_vars}")

        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Template variable not provided: {e}")

    def get_variables(self) -> list[str]:
        """Extract all variable names from template."""
        import re

        return re.findall(r"\{([^}]+)\}", self.template)


# Utility functions for working with AI models


def create_request_id() -> str:
    """Generate unique request ID."""
    import uuid

    return str(uuid.uuid4())


def estimate_tokens(text: str) -> int:
    """Rough estimation of token count for text."""
    # Very rough approximation: 1 token ≈ 4 characters
    # This is quite inaccurate but useful for quick estimates
    return len(text) // 4


def truncate_context(context: str, max_tokens: int) -> str:
    """Truncate context to fit within token limit."""
    estimated_tokens = estimate_tokens(context)
    if estimated_tokens <= max_tokens:
        return context

    # Rough truncation - in practice, you'd use proper tokenizer
    char_limit = max_tokens * 4
    if len(context) <= char_limit:
        return context

    # Truncate and add indicator
    truncated = context[: char_limit - 20]
    return truncated + "\n...[truncated]"


def sanitize_ai_response(response: str) -> str:
    """Clean and sanitize AI response text."""
    # Remove potential harmful content, excessive whitespace, etc.
    import re

    # Remove excessive whitespace
    response = re.sub(r"\n\s*\n", "\n\n", response)
    response = re.sub(r" +", " ", response)

    # Remove common AI disclaimers that add no value
    disclaimers = [
        "I'm an AI assistant",
        "As an AI language model",
        "I don't have personal opinions",
        "Please note that I'm an AI",
    ]

    for disclaimer in disclaimers:
        response = response.replace(disclaimer, "")

    return response.strip()
