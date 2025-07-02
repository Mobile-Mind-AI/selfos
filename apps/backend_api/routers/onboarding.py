"""
Onboarding flow API endpoints.
Handles the multi-step onboarding process for new users.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import datetime

from dependencies import get_db, get_current_user
from models import (
    OnboardingState, AssistantProfile, LifeArea, Goal, Task, User
)
from schemas.assistant_schemas import (
    OnboardingStep,
    OnboardingStepRequest,
    OnboardingStateOut,
    OnboardingStepResponse,
    AssistantCreationData,
    PersonalitySetupData,
    LanguagePreferencesData,
    LifeAreasSelectionData,
    FirstGoalData,
    PersonalityStyle,
    AssistantProfileCreate,
    AssistantProfileOut
)
from schemas import LifeAreaCreate, GoalCreate, TaskCreate

router = APIRouter(
    prefix="/onboarding",
    tags=["onboarding"]
)


@router.get("/state", response_model=OnboardingStateOut)
def get_onboarding_state(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current onboarding state for the user."""
    state = db.query(OnboardingState).filter(
        OnboardingState.user_id == current_user["uid"]
    ).first()
    
    if not state:
        # Create initial onboarding state
        state = OnboardingState(
            user_id=current_user["uid"],
            current_step=1,
            completed_steps=[]
        )
        db.add(state)
        db.commit()
        db.refresh(state)
    
    return state


@router.post("/step", response_model=OnboardingStepResponse)
def update_onboarding_step(
    request: OnboardingStepRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update onboarding progress for a specific step."""
    # Get or create onboarding state
    state = db.query(OnboardingState).filter(
        OnboardingState.user_id == current_user["uid"]
    ).first()
    
    if not state:
        state = OnboardingState(
            user_id=current_user["uid"],
            current_step=1,
            completed_steps=[]
        )
        db.add(state)
    
    # Update last activity
    state.last_activity = datetime.utcnow()
    
    # Process based on step type
    response_data = {}
    
    if request.step == OnboardingStep.ASSISTANT_CREATION:
        response_data = _handle_assistant_creation(request.data, state, current_user, db)
    elif request.step == OnboardingStep.PERSONALITY_SETUP:
        response_data = _handle_personality_setup(request.data, state, db)
    elif request.step == OnboardingStep.LANGUAGE_PREFERENCES:
        response_data = _handle_language_preferences(request.data, state, db)
    elif request.step == OnboardingStep.LIFE_AREAS:
        response_data = _handle_life_areas(request.data, state, current_user, db)
    elif request.step == OnboardingStep.FIRST_GOAL:
        response_data = _handle_first_goal(request.data, state, current_user, db)
    
    # Update completed steps
    step_number = _get_step_number(request.step)
    if step_number not in state.completed_steps:
        state.completed_steps = state.completed_steps + [step_number]
    
    # Update current step
    if step_number < 6:
        state.current_step = step_number + 1
    else:
        state.onboarding_completed = True
        state.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(state)
    
    return OnboardingStepResponse(
        success=True,
        current_step=state.current_step,
        completed_steps=state.completed_steps,
        next_step=state.current_step if not state.onboarding_completed else None,
        message=f"Step {request.step} completed successfully",
        data=response_data
    )


@router.post("/complete")
def complete_onboarding(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark onboarding as complete and prepare dashboard."""
    state = db.query(OnboardingState).filter(
        OnboardingState.user_id == current_user["uid"]
    ).first()
    
    if not state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Onboarding state not found"
        )
    
    # Verify all required steps are completed
    required_steps = [2, 3, 4, 5, 6]  # Skip welcome step
    missing_steps = [s for s in required_steps if s not in state.completed_steps]
    
    if missing_steps:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete onboarding. Missing steps: {missing_steps}"
        )
    
    state.onboarding_completed = True
    state.completed_at = datetime.utcnow()
    db.commit()
    
    # Get assistant for welcome message
    assistant = db.query(AssistantProfile).filter(
        AssistantProfile.id == state.assistant_profile_id
    ).first()
    
    welcome_message = f"Welcome! I'm {assistant.name if assistant else 'your assistant'}. "
    welcome_message += "I'm excited to help you achieve your goals. Let's get started!"
    
    return {
        "success": True,
        "onboarding_completed": True,
        "welcome_message": welcome_message,
        "dashboard_data": {
            "assistant_id": state.assistant_profile_id,
            "first_goal_id": state.first_goal_id,
            "first_task_id": state.first_task_id,
            "life_areas": state.selected_life_areas
        }
    }


@router.post("/skip")
def skip_onboarding(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Skip onboarding and create default setup."""
    # Create default assistant
    default_assistant = AssistantProfile(
        user_id=current_user["uid"],
        name="Assistant",
        style={
            "formality": 50,
            "directness": 50,
            "humor": 30,
            "empathy": 70,
            "motivation": 60
        },
        is_default=True
    )
    db.add(default_assistant)
    
    # Create or update onboarding state
    state = db.query(OnboardingState).filter(
        OnboardingState.user_id == current_user["uid"]
    ).first()
    
    if not state:
        state = OnboardingState(user_id=current_user["uid"])
        db.add(state)
    
    state.assistant_profile_id = default_assistant.id
    state.onboarding_completed = True
    state.completed_at = datetime.utcnow()
    state.skip_intro = True
    
    db.commit()
    
    return {
        "success": True,
        "message": "Onboarding skipped. Default assistant created.",
        "assistant_id": default_assistant.id
    }


# Helper functions

def _get_step_number(step: OnboardingStep) -> int:
    """Convert step enum to number."""
    step_map = {
        OnboardingStep.WELCOME: 1,
        OnboardingStep.ASSISTANT_CREATION: 2,
        OnboardingStep.PERSONALITY_SETUP: 3,
        OnboardingStep.LANGUAGE_PREFERENCES: 4,
        OnboardingStep.LIFE_AREAS: 5,
        OnboardingStep.FIRST_GOAL: 6,
        OnboardingStep.COMPLETION: 7
    }
    return step_map.get(step, 1)


def _handle_assistant_creation(
    data: Dict[str, Any],
    state: OnboardingState,
    current_user: dict,
    db: Session
) -> Dict[str, Any]:
    """Handle assistant creation step."""
    try:
        creation_data = AssistantCreationData(**data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid assistant creation data: {str(e)}"
        )
    
    # Store in temp data for later use
    state.temp_data = {
        **state.temp_data,
        "assistant_name": creation_data.name,
        "avatar_url": creation_data.avatar_url
    }
    
    return {"assistant_name": creation_data.name}


def _handle_personality_setup(
    data: Dict[str, Any],
    state: OnboardingState,
    db: Session
) -> Dict[str, Any]:
    """Handle personality setup step."""
    try:
        setup_data = PersonalitySetupData(**data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid personality data: {str(e)}"
        )
    
    # Store style in temp data
    state.temp_data = {
        **state.temp_data,
        "style": setup_data.style.dict()
    }
    
    return {"style": setup_data.style.dict()}


def _handle_language_preferences(
    data: Dict[str, Any],
    state: OnboardingState,
    db: Session
) -> Dict[str, Any]:
    """Handle language preferences step."""
    try:
        prefs_data = LanguagePreferencesData(**data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid language preferences: {str(e)}"
        )
    
    # Create the assistant profile with all collected data
    temp_data = state.temp_data or {}
    
    assistant = AssistantProfile(
        user_id=state.user_id,
        name=temp_data.get("assistant_name", "Assistant"),
        avatar_url=temp_data.get("avatar_url"),
        style=temp_data.get("style", {
            "formality": 50,
            "directness": 50,
            "humor": 30,
            "empathy": 70,
            "motivation": 60
        }),
        language=prefs_data.language.value,
        requires_confirmation=prefs_data.requires_confirmation,
        is_default=True
    )
    
    db.add(assistant)
    db.flush()
    
    state.assistant_profile_id = assistant.id
    
    return {"assistant_id": assistant.id}


def _handle_life_areas(
    data: Dict[str, Any],
    state: OnboardingState,
    current_user: dict,
    db: Session
) -> Dict[str, Any]:
    """Handle life areas selection step."""
    try:
        areas_data = LifeAreasSelectionData(**data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid life areas data: {str(e)}"
        )
    
    created_areas = []
    
    # Create custom life areas if provided
    if areas_data.custom_life_areas:
        for area_name in areas_data.custom_life_areas:
            life_area = LifeArea(
                user_id=current_user["uid"],
                name=area_name,
                weight=10
            )
            db.add(life_area)
            db.flush()
            created_areas.append(life_area.id)
    
    # Combine selected and created areas
    all_areas = areas_data.life_area_ids + created_areas
    state.selected_life_areas = all_areas
    
    return {"life_area_ids": all_areas}


def _handle_first_goal(
    data: Dict[str, Any],
    state: OnboardingState,
    current_user: dict,
    db: Session
) -> Dict[str, Any]:
    """Handle first goal creation step."""
    try:
        goal_data = FirstGoalData(**data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid goal data: {str(e)}"
        )
    
    # Create the goal
    goal = Goal(
        user_id=current_user["uid"],
        title=goal_data.title,
        description=goal_data.description,
        life_area_id=goal_data.life_area_id,
        status="todo",
        progress=0.0
    )
    db.add(goal)
    db.flush()
    
    state.first_goal_id = goal.id
    
    # Create a sample first task (in real implementation, this would use AI)
    if goal_data.generate_tasks:
        first_task = Task(
            user_id=current_user["uid"],
            goal_id=goal.id,
            life_area_id=goal_data.life_area_id,
            title=f"Start working on: {goal.title}",
            description="Take the first step towards your goal",
            status="todo",
            progress=0.0
        )
        db.add(first_task)
        db.flush()
        
        state.first_task_id = first_task.id
    
    return {
        "goal_id": goal.id,
        "task_id": state.first_task_id
    }


@router.get("/preview-personality")
def preview_personality(
    formality: int = 50,
    humor: int = 30,
    motivation: int = 60,
    current_user: dict = Depends(get_current_user)
):
    """Preview how the assistant will communicate with given personality settings."""
    # Generate sample responses based on personality
    samples = []
    
    if formality < 30:
        greeting = "Good day! How may I assist you today?"
    elif formality > 70:
        greeting = "Hey! What's up? How can I help?"
    else:
        greeting = "Hello! How can I help you today?"
    
    if humor > 70:
        greeting += " 😄"
    
    samples.append({"context": "greeting", "message": greeting})
    
    if motivation > 70:
        encouragement = "You're doing amazing! Every step counts. Let's crush those goals! 💪"
    elif motivation < 30:
        encouragement = "Take your time. Progress is progress."
    else:
        encouragement = "Great job! Keep up the good work."
    
    samples.append({"context": "encouragement", "message": encouragement})
    
    return {
        "personality": {
            "formality": formality,
            "humor": humor,
            "motivation": motivation
        },
        "samples": samples
    }