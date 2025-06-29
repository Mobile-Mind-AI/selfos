from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, TYPE_CHECKING
from datetime import datetime

from dependencies import get_db, get_current_user
from models import UserPreferences
from schemas import UserPreferencesCreate, UserPreferencesUpdate, UserPreferences as UserPreferencesSchema

if TYPE_CHECKING:
    from models import LifeArea

router = APIRouter(prefix="/user-preferences", tags=["user-preferences"])

@router.get("", response_model=UserPreferencesSchema)
def get_user_preferences(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's preferences"""
    user_id = current_user["uid"]
    
    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id
    ).first()
    
    if not preferences:
        # Create default preferences if none exist
        preferences = UserPreferences(user_id=user_id)
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
    
    return preferences

@router.post("", response_model=UserPreferencesSchema)
def create_user_preferences(
    preferences_data: UserPreferencesCreate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new user preferences (overwrites existing if any)"""
    user_id = current_user["uid"]
    
    # Check if preferences already exist
    existing_preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id
    ).first()
    
    if existing_preferences:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User preferences already exist. Use PUT to update."
        )
    
    # Validate default_life_area_id if provided
    if preferences_data.default_life_area_id:
        from models import LifeArea
        life_area = db.query(LifeArea).filter(
            LifeArea.id == preferences_data.default_life_area_id,
            LifeArea.user_id == user_id
        ).first()
        if not life_area:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Default life area not found or doesn't belong to user"
            )
    
    # Create new preferences
    preferences = UserPreferences(
        user_id=user_id,
        **preferences_data.dict(exclude_unset=True)
    )
    
    db.add(preferences)
    db.commit()
    db.refresh(preferences)
    
    return preferences

@router.put("", response_model=UserPreferencesSchema)
def update_user_preferences(
    preferences_update: UserPreferencesUpdate,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update existing user preferences"""
    user_id = current_user["uid"]
    
    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id
    ).first()
    
    if not preferences:
        # Create new preferences if none exist
        preferences = UserPreferences(
            user_id=user_id,
            **preferences_update.dict(exclude_unset=True)
        )
        db.add(preferences)
    else:
        # Update existing preferences
        update_data = preferences_update.dict(exclude_unset=True)
        
        # Validate default_life_area_id if provided  
        if 'default_life_area_id' in update_data and update_data['default_life_area_id'] is not None:
            from models import LifeArea
            life_area_id = update_data['default_life_area_id']
            if life_area_id > 0:  # Valid positive ID
                life_area = db.query(LifeArea).filter(
                    LifeArea.id == life_area_id,
                    LifeArea.user_id == user_id
                ).first()
                if not life_area:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Default life area not found or doesn't belong to user"
                    )
        for field, value in update_data.items():
            setattr(preferences, field, value)
        
        preferences.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(preferences)
    
    return preferences

@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_preferences(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reset user preferences to defaults (delete custom preferences)"""
    user_id = current_user["uid"]
    
    preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id
    ).first()
    
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User preferences not found"
        )
    
    db.delete(preferences)
    db.commit()

@router.get("/tone-options")
def get_tone_options():
    """Get available tone options"""
    return {
        "tone_options": [
            {"value": "friendly", "label": "Friendly", "description": "Warm and encouraging communication"},
            {"value": "coach", "label": "Coach", "description": "Motivational and goal-focused"},
            {"value": "minimal", "label": "Minimal", "description": "Brief and to-the-point"},
            {"value": "professional", "label": "Professional", "description": "Formal and business-like"}
        ]
    }

@router.get("/view-options")
def get_view_options():
    """Get available view mode options"""
    return {
        "view_options": [
            {"value": "list", "label": "List View", "description": "Simple list format"},
            {"value": "card", "label": "Card View", "description": "Visual card layout"},
            {"value": "timeline", "label": "Timeline View", "description": "Chronological timeline"}
        ]
    }

@router.post("/quick-setup", response_model=UserPreferencesSchema)
def quick_setup_preferences(
    tone: str,
    notifications: bool = True,
    default_view: str = "card",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Quick setup for new users with essential preferences"""
    user_id = current_user["uid"]
    
    # Validate tone option
    valid_tones = ["friendly", "coach", "minimal", "professional"]
    if tone not in valid_tones:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid tone. Must be one of: {', '.join(valid_tones)}"
        )
    
    # Validate view option
    valid_views = ["list", "card", "timeline"]
    if default_view not in valid_views:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid view. Must be one of: {', '.join(valid_views)}"
        )
    
    # Check if preferences already exist
    existing_preferences = db.query(UserPreferences).filter(
        UserPreferences.user_id == user_id
    ).first()
    
    if existing_preferences:
        # Update existing preferences
        existing_preferences.tone = tone
        existing_preferences.notifications_enabled = notifications
        existing_preferences.default_view = default_view
        existing_preferences.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(existing_preferences)
        return existing_preferences
    else:
        # Create new preferences
        preferences = UserPreferences(
            user_id=user_id,
            tone=tone,
            notifications_enabled=notifications,
            default_view=default_view
        )
        db.add(preferences)
        db.commit()
        db.refresh(preferences)
        return preferences