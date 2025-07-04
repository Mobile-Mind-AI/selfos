"""
Pydantic schemas for AI Assistant Profile management.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class SupportedLanguage(str, Enum):
    """Supported languages for assistant conversations."""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    CHINESE = "zh"
    JAPANESE = "ja"
    RUSSIAN = "ru"


class SupportedAIModel(str, Enum):
    """Supported AI models for assistants."""
    GPT_35_TURBO = "gpt-3.5-turbo"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    CLAUDE_3_HAIKU = "claude-3-haiku-20240307"
    CLAUDE_3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE_3_OPUS = "claude-3-opus-20240229"


class PersonalityStyle(BaseModel):
    """Personality style configuration (0-100 scale for each trait)."""
    formality: int = Field(..., ge=0, le=100, description="0 = very formal, 100 = extremely casual")
    directness: int = Field(..., ge=0, le=100, description="0 = very indirect, 100 = extremely direct")
    humor: int = Field(..., ge=0, le=100, description="0 = serious, 100 = humorous")
    empathy: int = Field(..., ge=0, le=100, description="0 = cold, 100 = warm and emotional")
    motivation: int = Field(..., ge=0, le=100, description="0 = passive, 100 = high-energy motivator")
    
    @validator('*')
    def validate_range(cls, v):
        """Ensure all values are within 0-100 range."""
        if isinstance(v, (int, float)):
            if v < 0 or v > 100:
                raise ValueError('Value must be between 0 and 100')
            return int(v)
        return v


class AssistantProfileBase(BaseModel):
    """Base schema for assistant profiles."""
    name: str = Field(..., min_length=1, max_length=100, description="Assistant name")
    description: Optional[str] = Field(None, max_length=500, description="Assistant description")
    avatar_url: Optional[str] = Field(None, max_length=500, description="Avatar image URL")
    ai_model: SupportedAIModel = Field(SupportedAIModel.GPT_35_TURBO, description="AI model to use")
    language: SupportedLanguage = Field(SupportedLanguage.ENGLISH, description="Primary language")
    requires_confirmation: bool = Field(True, description="Require user confirmation before taking actions")
    style: PersonalityStyle = Field(..., description="Personality style configuration")
    dialogue_temperature: float = Field(0.8, ge=0.0, le=2.0, description="Temperature for dialogue generation")
    intent_temperature: float = Field(0.3, ge=0.0, le=2.0, description="Temperature for intent classification")
    custom_instructions: Optional[str] = Field(None, max_length=1000, description="Custom behavior instructions")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate assistant name."""
        if not v or not v.strip():
            raise ValueError('Assistant name cannot be empty')
        return v.strip()
    
    @validator('description')
    def validate_description(cls, v):
        """Validate description."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v


class AssistantProfileCreate(AssistantProfileBase):
    """Schema for creating a new assistant profile."""
    is_default: bool = Field(False, description="Set as default assistant")


class AssistantProfileUpdate(BaseModel):
    """Schema for updating an assistant profile (all fields optional)."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    avatar_url: Optional[str] = Field(None, max_length=500)
    ai_model: Optional[SupportedAIModel] = None
    language: Optional[SupportedLanguage] = None
    requires_confirmation: Optional[bool] = None
    style: Optional[PersonalityStyle] = None
    dialogue_temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    intent_temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    custom_instructions: Optional[str] = Field(None, max_length=1000)
    is_default: Optional[bool] = None


class AssistantProfile(AssistantProfileBase):
    """Full assistant profile schema."""
    id: str = Field(..., description="Unique assistant profile ID")
    user_id: str = Field(..., description="Owner user ID")
    is_default: bool = Field(..., description="Whether this is the default assistant")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class AssistantProfileOut(AssistantProfile):
    """Enhanced assistant profile output schema."""
    pass


class OnboardingStep(str, Enum):
    """Onboarding flow steps."""
    WELCOME = "welcome"
    ASSISTANT_CREATION = "assistant_creation"
    PERSONALITY_SETUP = "personality_setup"
    LANGUAGE_PREFERENCES = "language_preferences"
    LIFE_AREAS = "life_areas"
    FIRST_GOAL = "first_goal"
    PERSONAL_CONFIG = "personal_config"  # New combined step for 3-step flow
    COMPLETION = "completion"


class OnboardingStepRequest(BaseModel):
    """Base request for any onboarding step."""
    step: OnboardingStep = Field(..., description="Current onboarding step")
    data: Dict[str, Any] = Field(..., description="Step-specific data")


class OnboardingStateOut(BaseModel):
    """Current onboarding state for a user."""
    id: str
    user_id: str
    current_step: int
    completed_steps: List[int]
    onboarding_completed: bool
    assistant_profile_id: Optional[str]
    selected_life_areas: List[int]
    first_goal_id: Optional[int]
    first_task_id: Optional[int]
    temp_data: Dict[str, Any] = Field(default_factory=dict)
    theme_preference: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    last_activity: datetime

    class Config:
        from_attributes = True


class AssistantCreationData(BaseModel):
    """Data for assistant creation step."""
    name: str = Field(..., min_length=1, max_length=100, description="Assistant name")
    avatar_url: Optional[str] = Field(None, max_length=500, description="Avatar image URL")


class PersonalitySetupData(BaseModel):
    """Data for personality setup step."""
    style: PersonalityStyle = Field(..., description="Personality style configuration")


class LanguagePreferencesData(BaseModel):
    """Data for language preferences step."""
    language: SupportedLanguage = Field(..., description="Primary language")
    requires_confirmation: bool = Field(True, description="Require confirmation for actions")


class LifeAreasSelectionData(BaseModel):
    """Data for life areas selection step."""
    life_area_ids: List[int] = Field(..., min_items=1, description="Selected life area IDs")
    custom_life_areas: Optional[List[str]] = Field(None, description="Custom life areas to create")


class FirstGoalData(BaseModel):
    """Data for first goal creation step."""
    skip_goal_creation: bool = Field(False, description="Skip goal creation and complete onboarding")
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Goal title")
    description: Optional[str] = Field(None, max_length=1000, description="Goal description")
    life_area_id: Optional[int] = Field(None, description="Associated life area")
    generate_tasks: bool = Field(True, description="Auto-generate tasks using AI")


class OnboardingRequest(BaseModel):
    """Request schema for assistant onboarding flow."""
    name: str = Field(..., min_length=1, max_length=100, description="Assistant name")
    avatar_url: Optional[str] = Field(None, max_length=500, description="Avatar image URL")
    style: PersonalityStyle = Field(..., description="Personality style configuration")
    language: SupportedLanguage = Field(SupportedLanguage.ENGLISH, description="Primary language")
    ai_model: Optional[SupportedAIModel] = Field(SupportedAIModel.GPT_35_TURBO, description="AI model preference")
    requires_confirmation: bool = Field(True, description="Require confirmation for actions")
    custom_instructions: Optional[str] = Field(None, max_length=1000, description="Custom instructions")


class OnboardingResponse(BaseModel):
    """Response schema for completed onboarding."""
    assistant_profile: AssistantProfileOut
    onboarding_completed: bool = True
    welcome_message: str


class OnboardingStepResponse(BaseModel):
    """Response for onboarding step updates."""
    success: bool
    current_step: int
    completed_steps: List[int]
    next_step: Optional[int]
    message: str
    data: Optional[Dict[str, Any]] = None


class AssistantConfigResponse(BaseModel):
    """Response schema for assistant configuration options."""
    supported_languages: Dict[str, str] = Field(..., description="Available languages")
    supported_models: Dict[str, str] = Field(..., description="Available AI models")
    default_style: PersonalityStyle = Field(..., description="Default personality style")
    temperature_ranges: Dict[str, Dict[str, float]] = Field(..., description="Temperature setting ranges")


class ChatWithAssistantRequest(BaseModel):
    """Request schema for chat with specific assistant."""
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    assistant_id: Optional[str] = Field(None, description="Specific assistant ID (uses default if not provided)")
    session_id: Optional[str] = Field(None, description="Conversation session ID")
    include_context: bool = Field(True, description="Include conversation context")


class PersonalityPreviewRequest(BaseModel):
    """Request schema for previewing personality changes."""
    style: PersonalityStyle = Field(..., description="Personality style to preview")
    sample_message: str = Field("How can I help you achieve your goals today?", max_length=200, description="Sample message to demonstrate style")


class PersonalityPreviewResponse(BaseModel):
    """Response schema for personality preview."""
    sample_response: str = Field(..., description="Sample response with applied personality")
    style_description: str = Field(..., description="Description of the personality style")
    personality_summary: Dict[str, str] = Field(..., description="Summary of each personality trait")