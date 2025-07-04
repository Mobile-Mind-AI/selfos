"""
Personal Configuration Pydantic Schemas

Data validation schemas for personal configuration endpoints:
- PersonalProfile (user stories and preferences)
- CustomLifeArea (user-created life categories)
- OnboardingAnalytics (tracking events)
- LifeAreaSuggestions (AI-powered recommendations)

Created for Phase 1.2 of enhanced onboarding implementation.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


# Enums for validation
class WorkStyle(str, Enum):
    """Work style preferences."""
    DEEP_WORK = "deep_work"
    COLLABORATIVE = "collaborative"
    FLEXIBLE = "flexible"
    STRUCTURED = "structured"


class CommunicationFrequency(str, Enum):
    """Communication frequency preferences."""
    DAILY = "daily"
    WEEKLY = "weekly"
    BI_WEEKLY = "bi_weekly"
    MONTHLY = "monthly"
    ON_DEMAND = "on_demand"


class GoalApproach(str, Enum):
    """Goal approach preferences."""
    STRUCTURED = "structured"
    FLEXIBLE = "flexible"
    EXPERIMENTAL = "experimental"
    MILESTONE_BASED = "milestone_based"


class MotivationStyle(str, Enum):
    """Motivation style preferences."""
    ACHIEVEMENT = "achievement"
    GROWTH = "growth"
    BALANCE = "balance"
    RECOGNITION = "recognition"


class EventType(str, Enum):
    """Analytics event types."""
    STEP_START = "step_start"
    STEP_COMPLETE = "step_complete"
    ABANDON = "abandon"
    ERROR = "error"
    SKIP = "skip"


# Personal Profile Schemas
class PersonalProfileBase(BaseModel):
    """Base personal profile schema."""
    # Personal information
    preferred_name: Optional[str] = Field(None, max_length=100, description="User's preferred name")
    avatar_id: Optional[str] = Field(None, max_length=100, description="Avatar ID reference")
    
    current_situation: Optional[str] = Field(None, max_length=2000, description="User's current life situation")
    interests: Optional[List[str]] = Field(default_factory=list, description="User's interests and hobbies")
    challenges: Optional[List[str]] = Field(default_factory=list, description="Current challenges they face")
    aspirations: Optional[List[str]] = Field(default_factory=list, description="What they hope to achieve")
    motivation: Optional[str] = Field(None, max_length=1000, description="What motivates them")

    # Preference learning fields
    work_style: Optional[WorkStyle] = Field(None, description="Preferred work style")
    communication_frequency: Optional[CommunicationFrequency] = Field(None, description="How often they want updates")
    goal_approach: Optional[GoalApproach] = Field(None, description="How they like to approach goals")
    motivation_style: Optional[MotivationStyle] = Field(None, description="What motivates them most")

    # Quick preferences and custom answers
    preferences: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Quick preferences from UI")
    custom_answers: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom answers to questions")
    
    # Selected standard life areas
    selected_life_areas: Optional[List[int]] = Field(default_factory=list, description="Selected standard life area IDs")

    # AI analysis storage
    story_analysis: Optional[Dict[str, Any]] = Field(default_factory=dict, description="AI analysis results")

    @validator('interests', 'challenges', 'aspirations')
    def validate_lists(cls, v):
        """Validate list fields."""
        if v is None:
            return []
        if len(v) > 20:
            raise ValueError("Maximum 20 items allowed")
        return [item.strip() for item in v if item.strip()]

    @validator('current_situation', 'motivation')
    def validate_text_fields(cls, v):
        """Validate text fields."""
        if v is not None:
            v = v.strip()
            # Allow empty strings for incomplete onboarding
            if v and len(v) < 10:
                raise ValueError("Must be at least 10 characters")
        return v
    
    @validator('preferred_name')
    def validate_preferred_name(cls, v):
        """Validate preferred name."""
        if v is not None:
            v = v.strip()
            # Allow empty strings for incomplete onboarding
        return v


class PersonalProfileCreate(PersonalProfileBase):
    """Schema for creating a personal profile."""
    pass


class PersonalProfileUpdate(BaseModel):
    """Schema for updating a personal profile."""
    preferred_name: Optional[str] = Field(None, max_length=100)
    avatar_id: Optional[str] = Field(None, max_length=100)
    current_situation: Optional[str] = Field(None, max_length=2000)
    interests: Optional[List[str]] = None
    challenges: Optional[List[str]] = None
    aspirations: Optional[List[str]] = None
    motivation: Optional[str] = Field(None, max_length=1000)
    work_style: Optional[WorkStyle] = None
    communication_frequency: Optional[CommunicationFrequency] = None
    goal_approach: Optional[GoalApproach] = None
    motivation_style: Optional[MotivationStyle] = None
    preferences: Optional[Dict[str, Any]] = None
    custom_answers: Optional[Dict[str, Any]] = None
    selected_life_areas: Optional[List[int]] = None
    story_analysis: Optional[Dict[str, Any]] = None


class PersonalProfileOut(PersonalProfileBase):
    """Schema for personal profile output."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Custom Life Area Schemas
class CustomLifeAreaBase(BaseModel):
    """Base custom life area schema."""
    name: str = Field(..., min_length=1, max_length=100, description="Life area name")
    icon: str = Field(default="category", max_length=50, description="Material icon name")
    color: str = Field(default="#6366f1", pattern=r'^#[0-9A-Fa-f]{6}$', description="Hex color code")
    description: Optional[str] = Field(None, max_length=500, description="Life area description")
    keywords: Optional[List[str]] = Field(default_factory=list, description="Keywords for AI understanding")

    @validator('name')
    def validate_name(cls, v):
        """Validate life area name."""
        v = v.strip()
        if len(v) < 1:
            raise ValueError("Name cannot be empty")
        return v

    @validator('keywords')
    def validate_keywords(cls, v):
        """Validate keywords list."""
        if v is None:
            return []
        if len(v) > 10:
            raise ValueError("Maximum 10 keywords allowed")
        return [keyword.strip().lower() for keyword in v if keyword.strip()]

    @validator('icon')
    def validate_icon(cls, v):
        """Validate icon name."""
        # Basic validation - could be expanded with actual Material icon list
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Icon must be a valid Material icon name")
        return v


class CustomLifeAreaCreate(CustomLifeAreaBase):
    """Schema for creating a custom life area."""
    is_custom: bool = Field(default=True, description="Whether this is a user-created area")


class CustomLifeAreaUpdate(BaseModel):
    """Schema for updating a custom life area."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    icon: Optional[str] = Field(None, max_length=50)
    color: Optional[str] = Field(None, pattern=r'^#[0-9A-Fa-f]{6}$')
    description: Optional[str] = Field(None, max_length=500)
    keywords: Optional[List[str]] = None
    priority_order: Optional[int] = Field(None, ge=1)


class CustomLifeAreaOut(CustomLifeAreaBase):
    """Schema for custom life area output."""
    id: int
    user_id: str
    priority_order: int
    is_custom: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Life Area Suggestion Schema
class LifeAreaSuggestionOut(BaseModel):
    """Schema for life area suggestions."""
    name: str
    icon: str
    color: str
    description: str
    keywords: List[str]
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="AI confidence in suggestion")
    reason: Optional[str] = Field(None, description="Why this area was suggested")


# Analytics Schemas
class OnboardingAnalyticsBase(BaseModel):
    """Base onboarding analytics schema."""
    session_id: str = Field(..., description="Unique session identifier")
    event_type: EventType = Field(..., description="Type of event")
    step_name: Optional[str] = Field(None, max_length=50, description="Name of the onboarding step")
    step_number: Optional[int] = Field(None, ge=1, le=10, description="Step number in flow")
    time_spent_seconds: Optional[int] = Field(None, ge=0, description="Time spent on step")
    completion_percentage: Optional[float] = Field(None, ge=0.0, le=100.0, description="Percentage completed")
    event_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional event data")

    @validator('session_id')
    def validate_session_id(cls, v):
        """Validate session ID format."""
        if len(v) < 8:
            raise ValueError("Session ID must be at least 8 characters")
        return v


class OnboardingAnalyticsCreate(OnboardingAnalyticsBase):
    """Schema for creating analytics event."""
    pass


class OnboardingAnalyticsOut(OnboardingAnalyticsBase):
    """Schema for analytics event output."""
    id: str
    user_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


# Story Analysis Schemas
class PersonalityInsights(BaseModel):
    """AI-generated personality insights."""
    dominant_traits: List[str] = Field(default_factory=list, description="Key personality traits")
    communication_style: Optional[str] = Field(None, description="Preferred communication style")
    motivation_type: Optional[str] = Field(None, description="Primary motivation driver")
    work_preferences: Optional[List[str]] = Field(default_factory=list, description="Work style preferences")
    goal_patterns: Optional[List[str]] = Field(default_factory=list, description="Goal-setting patterns")


class StoryAnalysisOut(BaseModel):
    """Schema for story analysis results."""
    personality_insights: PersonalityInsights
    suggested_life_areas: List[str] = Field(default_factory=list, description="Recommended life areas")
    potential_goals: List[str] = Field(default_factory=list, description="Suggested initial goals")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Analysis confidence")
    processing_notes: Optional[str] = Field(None, description="Additional analysis notes")


class StoryAnalysisRequest(BaseModel):
    """Schema for story analysis request."""
    story: str = Field(..., min_length=50, max_length=5000, description="Personal story to analyze")
    include_suggestions: bool = Field(default=True, description="Include life area and goal suggestions")
    analysis_depth: str = Field(default="standard", pattern="^(basic|standard|detailed)$", description="Analysis depth")

    @validator('story')
    def validate_story(cls, v):
        """Validate story content."""
        v = v.strip()
        if len(v) < 50:
            raise ValueError("Story must be at least 50 characters for meaningful analysis")
        return v


# Preference Learning Schemas
class PreferenceLearningData(BaseModel):
    """Schema for preference learning questionnaire data."""
    scenario_responses: Dict[str, Union[str, int, float]] = Field(
        default_factory=dict,
        description="Responses to scenario-based questions"
    )
    behavioral_indicators: Dict[str, Any] = Field(
        default_factory=dict,
        description="Behavioral patterns from interactions"
    )
    preference_weights: Dict[str, float] = Field(
        default_factory=dict,
        description="Calculated preference weights"
    )
    learning_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence in learned preferences")

    @validator('scenario_responses')
    def validate_scenario_responses(cls, v):
        """Validate scenario responses."""
        if len(v) > 50:
            raise ValueError("Maximum 50 scenario responses allowed")
        return v


# Comprehensive Configuration Schema
class PersonalConfigurationComplete(BaseModel):
    """Complete personal configuration for onboarding."""
    profile: PersonalProfileCreate
    life_areas: List[CustomLifeAreaCreate] = Field(default_factory=list, max_items=15)
    preferences: Optional[PreferenceLearningData] = None
    skip_ai_analysis: bool = Field(default=False, description="Skip AI story analysis")

    @validator('life_areas')
    def validate_life_areas(cls, v):
        """Validate life areas list."""
        if len(v) < 1:
            raise ValueError("At least one life area is required")
        # Check for duplicate names
        names = [area.name.lower() for area in v]
        if len(names) != len(set(names)):
            raise ValueError("Life area names must be unique")
        return v


# Response schemas for bulk operations
class BulkLifeAreaResponse(BaseModel):
    """Response for bulk life area operations."""
    created: List[CustomLifeAreaOut] = Field(default_factory=list)
    updated: List[CustomLifeAreaOut] = Field(default_factory=list)
    errors: List[Dict[str, str]] = Field(default_factory=list)
    total_processed: int


class PersonalConfigSummary(BaseModel):
    """Summary of user's personal configuration."""
    has_profile: bool
    life_areas_count: int
    has_preferences: bool
    completion_percentage: float = Field(ge=0.0, le=100.0)
    last_updated: Optional[datetime] = None
    missing_components: List[str] = Field(default_factory=list)