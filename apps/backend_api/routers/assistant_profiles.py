"""
Assistant Profiles API Router

Handles CRUD operations for AI assistant personality profiles.
Enables users to create, manage, and customize their AI assistants.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from dependencies import get_db, get_current_user
from models import AssistantProfile, User
from schemas.assistant_schemas import (
    AssistantProfileCreate, AssistantProfileUpdate, AssistantProfileOut,
    OnboardingRequest, OnboardingResponse, AssistantConfigResponse,
    PersonalityPreviewRequest, PersonalityPreviewResponse,
    SupportedLanguage, SupportedAIModel, PersonalityStyle
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/assistant_profiles", tags=["assistant_profiles"])


@router.get("/", response_model=List[AssistantProfileOut])
async def list_assistant_profiles(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of profiles to return"),
    offset: int = Query(0, ge=0, description="Number of profiles to skip"),
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all assistant profiles for the current user.
    """
    user_id = current_user["uid"]
    
    profiles = db.query(AssistantProfile).filter(
        AssistantProfile.user_id == user_id
    ).order_by(
        desc(AssistantProfile.is_default),  # Default profile first
        desc(AssistantProfile.created_at)
    ).offset(offset).limit(limit).all()
    
    return [AssistantProfileOut.from_orm(profile) for profile in profiles]


@router.get("/config", response_model=AssistantConfigResponse)
async def get_assistant_config():
    """
    Get configuration options for assistant profiles.
    Returns supported languages, models, and default settings.
    """
    return AssistantConfigResponse(
        supported_languages={
            "en": "English",
            "es": "Spanish", 
            "fr": "French",
            "de": "German",
            "it": "Italian",
            "pt": "Portuguese",
            "zh": "Chinese",
            "ja": "Japanese"
        },
        supported_models={
            "gpt-3.5-turbo": "GPT-3.5 Turbo (Fast & Efficient)",
            "gpt-4": "GPT-4 (Advanced Reasoning)",
            "gpt-4-turbo": "GPT-4 Turbo (Balanced Performance)",
            "claude-3-haiku-20240307": "Claude 3 Haiku (Quick & Concise)",
            "claude-3-sonnet-20240229": "Claude 3 Sonnet (Thoughtful & Detailed)",
            "claude-3-opus-20240229": "Claude 3 Opus (Most Capable)"
        },
        default_style=PersonalityStyle(
            formality=50,
            directness=50,
            humor=30,
            empathy=70,
            motivation=60
        ),
        temperature_ranges={
            "dialogue": {"min": 0.0, "max": 2.0, "default": 0.8},
            "intent": {"min": 0.0, "max": 1.0, "default": 0.3}
        }
    )


@router.get("/default", response_model=AssistantProfileOut)
async def get_default_assistant_profile(
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the user's default assistant profile.
    """
    user_id = current_user["uid"]
    
    profile = db.query(AssistantProfile).filter(
        and_(
            AssistantProfile.user_id == user_id,
            AssistantProfile.is_default == True
        )
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="No default assistant profile found")
    
    return AssistantProfileOut.from_orm(profile)


@router.post("/onboarding", response_model=OnboardingResponse)
async def complete_onboarding(
    request: OnboardingRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Complete assistant onboarding flow.
    Creates the user's first assistant profile and sets it as default.
    """
    user_id = current_user["uid"]
    
    # Check if user already has profiles
    existing_count = db.query(AssistantProfile).filter(
        AssistantProfile.user_id == user_id
    ).count()
    
    # Create new assistant profile
    profile = AssistantProfile(
        user_id=user_id,
        name=request.name,
        avatar_url=request.avatar_url,
        ai_model=request.ai_model,
        language=request.language,
        requires_confirmation=request.requires_confirmation,
        style=request.style.dict(),
        custom_instructions=request.custom_instructions,
        is_default=True  # First profile is always default
    )
    
    # If user already has profiles, unset their default status
    if existing_count > 0:
        db.query(AssistantProfile).filter(
            and_(
                AssistantProfile.user_id == user_id,
                AssistantProfile.is_default == True
            )
        ).update({"is_default": False})
    
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    # Generate welcome message based on personality
    welcome_message = await generate_welcome_message(profile, background_tasks)
    
    logger.info(f"Onboarding completed for user {user_id}: created assistant '{profile.name}'")
    
    return OnboardingResponse(
        assistant_profile=AssistantProfileOut.from_orm(profile),
        onboarding_completed=True,
        welcome_message=welcome_message
    )


@router.post("/", response_model=AssistantProfileOut)
async def create_assistant_profile(
    profile_data: AssistantProfileCreate,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new assistant profile.
    """
    user_id = current_user["uid"]
    
    # Check profile limit (max 5 profiles per user)
    existing_count = db.query(AssistantProfile).filter(
        AssistantProfile.user_id == user_id
    ).count()
    
    if existing_count >= 5:
        raise HTTPException(
            status_code=400, 
            detail="Maximum of 5 assistant profiles allowed per user"
        )
    
    # If setting as default, unset other default profiles
    if profile_data.is_default:
        db.query(AssistantProfile).filter(
            and_(
                AssistantProfile.user_id == user_id,
                AssistantProfile.is_default == True
            )
        ).update({"is_default": False})
    
    profile = AssistantProfile(
        user_id=user_id,
        name=profile_data.name,
        description=profile_data.description,
        avatar_url=profile_data.avatar_url,
        ai_model=profile_data.ai_model,
        language=profile_data.language,
        requires_confirmation=profile_data.requires_confirmation,
        style=profile_data.style.dict(),
        dialogue_temperature=profile_data.dialogue_temperature,
        intent_temperature=profile_data.intent_temperature,
        custom_instructions=profile_data.custom_instructions,
        is_default=profile_data.is_default or existing_count == 0  # First profile becomes default
    )
    
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    logger.info(f"Created assistant profile '{profile.name}' for user {user_id}")
    
    return AssistantProfileOut.from_orm(profile)


@router.get("/{profile_id}", response_model=AssistantProfileOut)
async def get_assistant_profile(
    profile_id: str,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific assistant profile by ID.
    """
    user_id = current_user["uid"]
    
    profile = db.query(AssistantProfile).filter(
        and_(
            AssistantProfile.id == profile_id,
            AssistantProfile.user_id == user_id
        )
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Assistant profile not found")
    
    return AssistantProfileOut.from_orm(profile)


@router.patch("/{profile_id}", response_model=AssistantProfileOut)
async def update_assistant_profile(
    profile_id: str,
    profile_data: AssistantProfileUpdate,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing assistant profile.
    """
    user_id = current_user["uid"]
    
    profile = db.query(AssistantProfile).filter(
        and_(
            AssistantProfile.id == profile_id,
            AssistantProfile.user_id == user_id
        )
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Assistant profile not found")
    
    # Update fields that were provided
    update_data = profile_data.dict(exclude_unset=True)
    
    # Handle default profile logic
    if "is_default" in update_data and update_data["is_default"]:
        # Unset other default profiles
        db.query(AssistantProfile).filter(
            and_(
                AssistantProfile.user_id == user_id,
                AssistantProfile.is_default == True,
                AssistantProfile.id != profile_id
            )
        ).update({"is_default": False})
    
    # Convert style object to dict if provided
    if "style" in update_data and update_data["style"]:
        update_data["style"] = update_data["style"].dict()
    
    # Apply updates
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    
    logger.info(f"Updated assistant profile '{profile.name}' for user {user_id}")
    
    return AssistantProfileOut.from_orm(profile)


@router.delete("/{profile_id}")
async def delete_assistant_profile(
    profile_id: str,
    current_user: Dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an assistant profile.
    Cannot delete the default profile if it's the only one.
    """
    user_id = current_user["uid"]
    
    profile = db.query(AssistantProfile).filter(
        and_(
            AssistantProfile.id == profile_id,
            AssistantProfile.user_id == user_id
        )
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Assistant profile not found")
    
    # Check if this is the only profile
    total_profiles = db.query(AssistantProfile).filter(
        AssistantProfile.user_id == user_id
    ).count()
    
    if total_profiles <= 1:
        raise HTTPException(
            status_code=400, 
            detail="Cannot delete the only assistant profile"
        )
    
    # If deleting default profile, set another as default
    if profile.is_default:
        next_profile = db.query(AssistantProfile).filter(
            and_(
                AssistantProfile.user_id == user_id,
                AssistantProfile.id != profile_id
            )
        ).first()
        
        if next_profile:
            next_profile.is_default = True
    
    db.delete(profile)
    db.commit()
    
    logger.info(f"Deleted assistant profile '{profile.name}' for user {user_id}")
    
    return {"message": "Assistant profile deleted successfully"}


@router.post("/preview", response_model=PersonalityPreviewResponse)
async def preview_personality(
    request: PersonalityPreviewRequest,
    current_user: Dict = Depends(get_current_user)
):
    """
    Preview how a personality style would affect responses.
    Returns a sample response with the specified personality applied.
    """
    style = request.style
    
    # Generate personality description
    traits = []
    if style.formality < 30:
        traits.append("formal and professional")
    elif style.formality > 70:
        traits.append("casual and relaxed")
    else:
        traits.append("conversational")
    
    if style.directness > 70:
        traits.append("direct and straightforward")
    elif style.directness < 30:
        traits.append("gentle and diplomatic")
    
    if style.humor > 60:
        traits.append("playful and humorous")
    elif style.humor < 20:
        traits.append("serious and focused")
    
    if style.empathy > 80:
        traits.append("warm and understanding")
    elif style.empathy < 30:
        traits.append("analytical and objective")
    
    if style.motivation > 80:
        traits.append("energetic and encouraging")
    elif style.motivation < 30:
        traits.append("calm and supportive")
    
    style_description = f"This assistant is {', '.join(traits)}."
    
    # Generate sample response
    sample_response = generate_personality_sample(style, request.sample_message)
    
    # Create personality summary
    personality_summary = {
        "formality": describe_trait_level(style.formality, "formal", "casual"),
        "directness": describe_trait_level(style.directness, "diplomatic", "direct"),
        "humor": describe_trait_level(style.humor, "serious", "playful"),
        "empathy": describe_trait_level(style.empathy, "analytical", "empathetic"),
        "motivation": describe_trait_level(style.motivation, "calm", "energetic")
    }
    
    return PersonalityPreviewResponse(
        sample_response=sample_response,
        style_description=style_description,
        personality_summary=personality_summary
    )


# Helper functions

async def generate_welcome_message(profile: AssistantProfile, background_tasks: BackgroundTasks) -> str:
    """Generate a personalized welcome message based on the assistant's personality."""
    style = profile.style
    name = profile.name
    
    # Base welcome message
    welcome = f"Hello! I'm {name}, your personal assistant."
    
    # Adjust based on personality
    if style.get("formality", 50) > 70:
        welcome = f"Hey there! I'm {name}, and I'm super excited to be your personal assistant!"
    elif style.get("formality", 50) < 30:
        welcome = f"Good day. I am {name}, your designated personal assistant."
    
    # Add personality-specific elements
    if style.get("empathy", 50) > 70:
        welcome += " I'm here to understand your needs and support you every step of the way."
    
    if style.get("motivation", 50) > 70:
        welcome += " Let's achieve amazing things together!"
    elif style.get("motivation", 50) > 50:
        welcome += " I'm ready to help you reach your goals."
    else:
        welcome += " I'm available whenever you need assistance."
    
    if style.get("humor", 50) > 60:
        welcome += " (And don't worry, I promise to keep things interesting! 😊)"
    
    return welcome


def generate_personality_sample(style: PersonalityStyle, base_message: str) -> str:
    """Generate a sample response with personality applied."""
    response = base_message
    
    # Adjust formality
    if style.formality > 70:
        response = response.replace("How can I help", "How can I help ya")
        response = response.replace("achieve", "crush")
        response += " Let's dive in!"
    elif style.formality < 30:
        response = "I would be pleased to assist you in achieving your objectives today."
    
    # Add humor
    if style.humor > 60:
        response += " Ready to make some magic happen? ✨"
    elif style.humor > 40:
        response += " What's on your agenda today?"
    
    # Add empathy
    if style.empathy > 80:
        response = response.replace("How can I help", "I'm here for you - how can I help")
        response += " I care about your success and wellbeing."
    elif style.empathy < 30:
        response = "Please specify your requirements for today's session."
    
    # Add motivation
    if style.motivation > 80:
        response += " You've got this! 🚀"
    elif style.motivation > 60:
        response += " I believe in your ability to achieve great things."
    
    return response


def describe_trait_level(value: int, low_desc: str, high_desc: str) -> str:
    """Describe a personality trait level."""
    if value < 20:
        return f"Very {low_desc}"
    elif value < 40:
        return f"Somewhat {low_desc}"
    elif value < 60:
        return "Balanced"
    elif value < 80:
        return f"Somewhat {high_desc}"
    else:
        return f"Very {high_desc}"