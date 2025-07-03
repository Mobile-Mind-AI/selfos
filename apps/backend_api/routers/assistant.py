"""
Assistant profile management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from dependencies import get_db, get_current_user
import models
from schemas.assistant_schemas import (
    AssistantProfile,
    AssistantProfileCreate,
    AssistantProfileUpdate,
    AssistantProfileOut,
    SupportedLanguage,
    SupportedAIModel,
    PersonalityStyle
)

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


@router.get("/profile", response_model=AssistantProfileOut)
def get_current_assistant_profile(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current user's default assistant profile.
    
    Returns:
        Current assistant profile
    """
    # Get default assistant profile
    profile = db.query(models.AssistantProfile).filter(
        models.AssistantProfile.user_id == current_user["uid"],
        models.AssistantProfile.is_default == True
    ).first()
    
    if not profile:
        # If no default profile exists, get the first profile or create one
        profile = db.query(models.AssistantProfile).filter(
            models.AssistantProfile.user_id == current_user["uid"]
        ).first()
        
        if not profile:
            # Create default profile
            profile = models.AssistantProfile(
                user_id=current_user["uid"],
                name="Assistant",
                avatar_url="ai_robot_blue",
                is_default=True
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
    
    return profile


@router.put("/profile", response_model=AssistantProfileOut)
def update_assistant_profile(
    update_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the current user's assistant profile.
    
    Args:
        update_data: Fields to update
        
    Returns:
        Updated assistant profile
    """
    # Get current profile
    profile = db.query(models.AssistantProfile).filter(
        models.AssistantProfile.user_id == current_user["uid"],
        models.AssistantProfile.is_default == True
    ).first()
    
    if not profile:
        # Create new profile if none exists
        profile = models.AssistantProfile(
            user_id=current_user["uid"],
            is_default=True
        )
        db.add(profile)
    
    # Update fields
    for field, value in update_data.items():
        if hasattr(profile, field) and value is not None:
            setattr(profile, field, value)
    
    profile.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(profile)
    
    return profile


@router.post("/profile", response_model=AssistantProfileOut)
def create_assistant_profile(
    profile_data: AssistantProfileCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new assistant profile.
    
    Args:
        profile_data: Assistant profile data
        
    Returns:
        Created assistant profile
    """
    # If this is set as default, unset other default profiles
    if profile_data.is_default:
        db.query(models.AssistantProfile).filter(
            models.AssistantProfile.user_id == current_user["uid"],
            models.AssistantProfile.is_default == True
        ).update({"is_default": False})
    
    # Create new profile
    profile = models.AssistantProfile(
        user_id=current_user["uid"],
        **profile_data.dict()
    )
    
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return profile


@router.get("/profiles", response_model=List[AssistantProfileOut])
def list_assistant_profiles(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all assistant profiles for the current user.
    
    Returns:
        List of assistant profiles
    """
    profiles = db.query(models.AssistantProfile).filter(
        models.AssistantProfile.user_id == current_user["uid"]
    ).order_by(
        models.AssistantProfile.is_default.desc(),
        models.AssistantProfile.created_at.desc()
    ).all()
    
    return profiles


@router.get("/profiles/{profile_id}", response_model=AssistantProfileOut)
def get_assistant_profile(
    profile_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific assistant profile.
    
    Args:
        profile_id: Assistant profile ID
        
    Returns:
        Assistant profile
    """
    profile = db.query(models.AssistantProfile).filter(
        models.AssistantProfile.id == profile_id,
        models.AssistantProfile.user_id == current_user["uid"]
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant profile not found"
        )
    
    return profile


@router.put("/profiles/{profile_id}", response_model=AssistantProfileOut)
def update_specific_assistant_profile(
    profile_id: str,
    update_data: AssistantProfileUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a specific assistant profile.
    
    Args:
        profile_id: Assistant profile ID
        update_data: Fields to update
        
    Returns:
        Updated assistant profile
    """
    profile = db.query(models.AssistantProfile).filter(
        models.AssistantProfile.id == profile_id,
        models.AssistantProfile.user_id == current_user["uid"]
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant profile not found"
        )
    
    # If setting as default, unset other defaults
    if update_data.is_default:
        db.query(models.AssistantProfile).filter(
            models.AssistantProfile.user_id == current_user["uid"],
            models.AssistantProfile.is_default == True,
            models.AssistantProfile.id != profile_id
        ).update({"is_default": False})
    
    # Update fields
    for field, value in update_data.dict(exclude_unset=True).items():
        if hasattr(profile, field):
            setattr(profile, field, value)
    
    profile.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(profile)
    
    return profile


@router.delete("/profiles/{profile_id}")
def delete_assistant_profile(
    profile_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete an assistant profile.
    
    Args:
        profile_id: Assistant profile ID to delete
        
    Returns:
        Success message
    """
    profile = db.query(models.AssistantProfile).filter(
        models.AssistantProfile.id == profile_id,
        models.AssistantProfile.user_id == current_user["uid"]
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant profile not found"
        )
    
    # Don't allow deletion of the last/only profile
    total_profiles = db.query(models.AssistantProfile).filter(
        models.AssistantProfile.user_id == current_user["uid"]
    ).count()
    
    if total_profiles <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete the last assistant profile"
        )
    
    # If deleting default profile, set another as default
    if profile.is_default:
        new_default = db.query(models.AssistantProfile).filter(
            models.AssistantProfile.user_id == current_user["uid"],
            models.AssistantProfile.id != profile_id
        ).first()
        
        if new_default:
            new_default.is_default = True
    
    db.delete(profile)
    db.commit()
    
    return {"message": "Assistant profile deleted successfully", "profile_id": profile_id}


@router.post("/profiles/{profile_id}/set-default")
def set_default_assistant_profile(
    profile_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Set an assistant profile as the default.
    
    Args:
        profile_id: Assistant profile ID to set as default
        
    Returns:
        Success message
    """
    profile = db.query(models.AssistantProfile).filter(
        models.AssistantProfile.id == profile_id,
        models.AssistantProfile.user_id == current_user["uid"]
    ).first()
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assistant profile not found"
        )
    
    # Unset all other defaults
    db.query(models.AssistantProfile).filter(
        models.AssistantProfile.user_id == current_user["uid"],
        models.AssistantProfile.is_default == True
    ).update({"is_default": False})
    
    # Set this as default
    profile.is_default = True
    db.commit()
    
    return {"message": "Assistant profile set as default", "profile_id": profile_id}


@router.get("/config")
def get_assistant_config():
    """
    Get assistant configuration options (languages, models, etc.).
    
    Returns:
        Configuration options
    """
    return {
        "supported_languages": {
            "en": "English",
            "es": "Español", 
            "fr": "Français",
            "de": "Deutsch",
            "it": "Italiano",
            "pt": "Português",
            "zh": "中文",
            "ja": "日本語",
            "ru": "Русский"
        },
        "supported_models": {
            "gpt-3.5-turbo": "GPT-3.5 Turbo",
            "gpt-4": "GPT-4",
            "gpt-4-turbo": "GPT-4 Turbo",
            "claude-3-haiku-20240307": "Claude 3 Haiku",
            "claude-3-sonnet-20240229": "Claude 3 Sonnet",
            "claude-3-opus-20240229": "Claude 3 Opus"
        },
        "default_style": {
            "formality": 50,
            "directness": 50,
            "humor": 30,
            "empathy": 70,
            "motivation": 60
        },
        "temperature_ranges": {
            "dialogue": {"min": 0.0, "max": 2.0, "default": 0.8},
            "intent": {"min": 0.0, "max": 2.0, "default": 0.3}
        }
    }