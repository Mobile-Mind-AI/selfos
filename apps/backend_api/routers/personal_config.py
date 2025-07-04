"""
Personal Configuration API Router

Handles personal configuration endpoints for enhanced onboarding:
- Personal profiles and stories
- Custom life areas with icons/colors
- Preference learning data
- Analytics tracking

"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from dependencies import get_db
from models import User, PersonalProfile, CustomLifeArea, OnboardingAnalytics
from dependencies import get_current_user
from schemas.personal_config_schemas import (
    PersonalProfileCreate,
    PersonalProfileOut,
    PersonalProfileUpdate,
    CustomLifeAreaCreate,
    CustomLifeAreaOut,
    CustomLifeAreaUpdate,
    OnboardingAnalyticsCreate,
    OnboardingAnalyticsOut,
    LifeAreaSuggestionOut
)

router = APIRouter(tags=["personal-config"])

# Personal Profile Endpoints
@router.post("/profile", response_model=PersonalProfileOut)
async def create_personal_profile(
        profile_data: PersonalProfileCreate,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Create or update user's personal profile with story and preferences."""
    
    try:
        print(f"🔍 PERSONAL_CONFIG: Received profile data: {profile_data.dict()}")
        print(f"🔍 PERSONAL_CONFIG: User ID: {current_user['uid']}")

        # Check if profile already exists
        existing_profile = db.query(PersonalProfile).filter(
            PersonalProfile.user_id == current_user["uid"]
        ).first()

        if existing_profile:
            print(f"🔄 PERSONAL_CONFIG: Updating existing profile for user {current_user['uid']}")
            # Update existing profile
            for field, value in profile_data.dict(exclude_unset=True).items():
                print(f"🔄 PERSONAL_CONFIG: Setting {field} = {value}")
                setattr(existing_profile, field, value)
            existing_profile.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(existing_profile)
            print(f"✅ PERSONAL_CONFIG: Profile updated successfully")
            return existing_profile

        # Create new profile
        print(f"🆕 PERSONAL_CONFIG: Creating new profile for user {current_user['uid']}")
        profile_dict = profile_data.dict()
        print(f"🆕 PERSONAL_CONFIG: Profile dict: {profile_dict}")
        
        new_profile = PersonalProfile(
            id=str(uuid.uuid4()),
            user_id=current_user["uid"],
            **profile_dict
        )

        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)
        print(f"✅ PERSONAL_CONFIG: New profile created successfully")

        return new_profile
        
    except Exception as e:
        print(f"🔴 PERSONAL_CONFIG: Error creating/updating profile: {e}")
        print(f"🔴 PERSONAL_CONFIG: Profile data: {profile_data}")
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail=f"Failed to create/update profile: {str(e)}"
        )


@router.get("/profile", response_model=Optional[PersonalProfileOut])
async def get_personal_profile(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get user's personal profile."""
    
    print("🚨🚨🚨 GET_PROFILE ENDPOINT CALLED! 🚨🚨🚨")

    profile = db.query(PersonalProfile).filter(
        PersonalProfile.user_id == current_user["uid"]
    ).first()
    
    if profile:
        print(f"🔍 GET_PROFILE: Found profile for user {current_user['uid']}")
        print(f"🔍 GET_PROFILE: avatar_id = {repr(profile.avatar_id)}")
        print(f"🔍 GET_PROFILE: selected_life_areas = {profile.selected_life_areas}")
        print(f"🔍 GET_PROFILE: Full profile dict: {profile.__dict__}")
        
        # Test direct serialization
        from schemas.personal_config_schemas import PersonalProfileOut
        try:
            # Use Pydantic v2 method
            serialized = PersonalProfileOut.model_validate(profile)
            print(f"🔍 GET_PROFILE: Serialized avatar_id = {repr(serialized.avatar_id)}")
            print(f"🔍 GET_PROFILE: Serialized selected_life_areas = {serialized.selected_life_areas}")
        except Exception as e:
            print(f"🔍 GET_PROFILE: Serialization error: {e}")
    else:
        print(f"🔍 GET_PROFILE: No profile found for user {current_user['uid']}")

    return profile


@router.put("/profile", response_model=PersonalProfileOut)
async def update_personal_profile(
        profile_update: PersonalProfileUpdate,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Update user's personal profile."""

    profile = db.query(PersonalProfile).filter(
        PersonalProfile.user_id == current_user["uid"]
    ).first()

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Personal profile not found"
        )

    # Update fields
    for field, value in profile_update.dict(exclude_unset=True).items():
        setattr(profile, field, value)
    profile.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(profile)

    return profile


# Custom Life Areas Endpoints
@router.get("/life-areas", response_model=List[CustomLifeAreaOut])
async def get_custom_life_areas(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get user's custom life areas ordered by priority."""

    life_areas = db.query(CustomLifeArea).filter(
        CustomLifeArea.user_id == current_user["uid"]
    ).order_by(CustomLifeArea.priority_order).all()

    return life_areas


@router.post("/life-areas", response_model=CustomLifeAreaOut)
async def create_custom_life_area(
        life_area_data: CustomLifeAreaCreate,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Create a new custom life area."""

    # Get next priority order
    max_priority = db.query(CustomLifeArea).filter(
        CustomLifeArea.user_id == current_user["uid"]
    ).count()

    new_life_area = CustomLifeArea(
        user_id=current_user["uid"],
        priority_order=max_priority + 1,
        **life_area_data.dict()
    )

    db.add(new_life_area)
    db.commit()
    db.refresh(new_life_area)

    return new_life_area


@router.put("/life-areas/{life_area_id}", response_model=CustomLifeAreaOut)
async def update_custom_life_area(
        life_area_id: int,
        life_area_update: CustomLifeAreaUpdate,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Update a custom life area."""

    life_area = db.query(CustomLifeArea).filter(
        CustomLifeArea.id == life_area_id,
        CustomLifeArea.user_id == current_user["uid"]
    ).first()

    if not life_area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Life area not found"
        )

    # Update fields
    for field, value in life_area_update.dict(exclude_unset=True).items():
        setattr(life_area, field, value)
    life_area.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(life_area)

    return life_area


@router.delete("/life-areas/{life_area_id}")
async def delete_custom_life_area(
        life_area_id: int,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Delete a custom life area."""

    life_area = db.query(CustomLifeArea).filter(
        CustomLifeArea.id == life_area_id,
        CustomLifeArea.user_id == current_user["uid"]
    ).first()

    if not life_area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Life area not found"
        )

    db.delete(life_area)
    db.commit()

    return {"message": "Life area deleted successfully"}


@router.put("/life-areas/reorder")
async def reorder_life_areas(
        area_ids: List[int],
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Reorder life areas by priority."""

    # Validate all areas belong to user
    user_areas = db.query(CustomLifeArea).filter(
        CustomLifeArea.user_id == current_user["uid"],
        CustomLifeArea.id.in_(area_ids)
    ).all()

    if len(user_areas) != len(area_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Some life areas not found or don't belong to user"
        )

    # Update priority order
    for index, area_id in enumerate(area_ids):
        db.query(CustomLifeArea).filter(
            CustomLifeArea.id == area_id,
            CustomLifeArea.user_id == current_user["uid"]
        ).update({"priority_order": index + 1})

    db.commit()

    return {"message": "Life areas reordered successfully"}


# Life Area Suggestions
@router.get("/life-areas/suggestions", response_model=List[LifeAreaSuggestionOut])
async def get_life_area_suggestions(
        interests: Optional[str] = None,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get AI-powered life area suggestions based on user interests."""

    # For now, return static suggestions
    # TODO: Integrate with AI service for personalized suggestions

    base_suggestions = [
        LifeAreaSuggestionOut(
            name="Health & Wellness",
            icon="fitness_center",
            color="#ef4444",
            description="Physical health, mental wellness, and self-care",
            keywords=["fitness", "nutrition", "mental health", "wellness"]
        ),
        LifeAreaSuggestionOut(
            name="Work & Career",
            icon="work",
            color="#3b82f6",
            description="Professional development and career growth",
            keywords=["career", "professional", "work", "skills"]
        ),
        LifeAreaSuggestionOut(
            name="Relationships",
            icon="people",
            color="#ec4899",
            description="Family, friends, and social connections",
            keywords=["family", "friends", "social", "relationships"]
        ),
        LifeAreaSuggestionOut(
            name="Personal Growth",
            icon="psychology",
            color="#8b5cf6",
            description="Learning, self-improvement, and personal development",
            keywords=["learning", "growth", "development", "skills"]
        ),
        LifeAreaSuggestionOut(
            name="Finances",
            icon="account_balance",
            color="#10b981",
            description="Financial planning, budgeting, and investments",
            keywords=["money", "budget", "savings", "investments"]
        ),
    ]

    # Filter out areas user already has
    existing_areas = db.query(CustomLifeArea.name).filter(
        CustomLifeArea.user_id == current_user["uid"]
    ).all()
    existing_names = {area.name for area in existing_areas}

    suggestions = [
        suggestion for suggestion in base_suggestions
        if suggestion.name not in existing_names
    ]

    return suggestions


# Analytics Endpoints
@router.post("/analytics", response_model=OnboardingAnalyticsOut)
async def track_onboarding_event(
        analytics_data: OnboardingAnalyticsCreate,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Track onboarding analytics event."""

    analytics_event = OnboardingAnalytics(
        id=str(uuid.uuid4()),
        user_id=current_user["uid"],
        **analytics_data.dict()
    )

    db.add(analytics_event)
    db.commit()
    db.refresh(analytics_event)

    return analytics_event


@router.get("/analytics/summary")
async def get_analytics_summary(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Get onboarding analytics summary for current user."""

    analytics = db.query(OnboardingAnalytics).filter(
        OnboardingAnalytics.user_id == current_user["uid"]
    ).all()

    # Calculate summary metrics
    total_events = len(analytics)
    step_counts = {}
    total_time = 0

    for event in analytics:
        step_name = event.step_name or "unknown"
        step_counts[step_name] = step_counts.get(step_name, 0) + 1
        if event.time_spent_seconds:
            total_time += event.time_spent_seconds

    return {
        "total_events": total_events,
        "step_counts": step_counts,
        "total_time_seconds": total_time,
        "average_time_per_step": total_time / max(total_events, 1)
    }


# Story Analysis (Future AI Integration)
@router.post("/story/analyze")
async def analyze_personal_story(
        story: str,
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Analyze personal story for insights and suggestions."""

    # TODO: Integrate with AI service for story analysis
    # For now, return mock analysis

    mock_analysis = {
        "personality_insights": {
            "dominant_traits": ["goal-oriented", "analytical", "growth-minded"],
            "communication_style": "direct",
            "motivation_type": "achievement"
        },
        "suggested_life_areas": [
            "Personal Growth",
            "Work & Career",
            "Health & Wellness"
        ],
        "potential_goals": [
            "Develop leadership skills",
            "Improve work-life balance",
            "Learn new technical skills"
        ],
        "confidence_score": 0.85
    }

    return mock_analysis


# Health Check
@router.get("/health")
async def health_check():
    """Health check for personal configuration endpoints."""
    return {
        "status": "healthy",
        "service": "personal-config",
        "endpoints": [
            "profile",
            "life-areas",
            "analytics",
            "story/analyze"
        ]
    }