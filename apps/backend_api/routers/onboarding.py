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
    print(f"🔍 BACKEND: Getting onboarding state for user {current_user['uid']}")
    
    state = db.query(OnboardingState).filter(
        OnboardingState.user_id == current_user["uid"]
    ).first()
    
    if not state:
        print(f"🔍 BACKEND: No onboarding state found, creating new one")
        # Create initial onboarding state
        state = OnboardingState(
            user_id=current_user["uid"],
            current_step=1,
            completed_steps=[]
        )
        db.add(state)
        db.commit()
        db.refresh(state)
    else:
        print(f"🔍 BACKEND: Found onboarding state - completed: {state.onboarding_completed}, steps: {state.completed_steps}")
    
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
        # Handle combined assistant creation (includes personality and language)
        response_data = _handle_assistant_creation(request.data, state, current_user, db)
        # Since assistant creation now includes personality and language, mark those steps as complete too
        if 3 not in state.completed_steps:
            state.completed_steps = state.completed_steps + [3]
        if 4 not in state.completed_steps:
            state.completed_steps = state.completed_steps + [4]
    elif request.step == OnboardingStep.PERSONALITY_SETUP:
        response_data = _handle_personality_setup(request.data, state, db)
    elif request.step == OnboardingStep.LANGUAGE_PREFERENCES:
        response_data = _handle_language_preferences(request.data, state, db)
    elif request.step == OnboardingStep.LIFE_AREAS:
        response_data = _handle_life_areas(request.data, state, current_user, db)
    elif request.step == OnboardingStep.FIRST_GOAL:
        response_data = _handle_first_goal(request.data, state, current_user, db)
    elif request.step == OnboardingStep.PERSONAL_CONFIG:
        response_data = _handle_personal_config(request.data, state, current_user, db)
    
    # Update completed steps
    step_number = _get_step_number(request.step)
    print(f"🎯 ONBOARDING: Processing step {request.step} (number {step_number})")
    print(f"🎯 ONBOARDING: Current completed_steps before: {state.completed_steps}")
    
    if step_number not in state.completed_steps:
        state.completed_steps = state.completed_steps + [step_number]
        print(f"🎯 ONBOARDING: Added step {step_number} to completed_steps: {state.completed_steps}")
    
    # Update current step
    if step_number < 6:
        state.current_step = step_number + 1
        print(f"🎯 ONBOARDING: Updated current_step to: {state.current_step}")
    else:
        state.onboarding_completed = True
        state.completed_at = datetime.utcnow()
        print(f"🎯 ONBOARDING: Marked onboarding as completed (step {step_number} >= 6)")
    
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
    
    print(f"🎯 ONBOARDING: Complete requested for user {current_user['uid']}")
    print(f"🎯 ONBOARDING: Current state - completed_steps: {state.completed_steps}, onboarding_completed: {state.onboarding_completed}")
    print(f"🎯 ONBOARDING: Assistant profile ID: {state.assistant_profile_id}")
    print(f"🎯 ONBOARDING: Selected life areas: {state.selected_life_areas}")
    
    # Verify required steps are completed (more flexible approach)
    has_assistant = state.assistant_profile_id is not None
    has_life_areas = state.selected_life_areas and len(state.selected_life_areas) > 0
    has_basic_steps = len(state.completed_steps) >= 2  # At least assistant and life areas
    
    print(f"🎯 ONBOARDING: Validation - has_assistant: {has_assistant}, has_life_areas: {has_life_areas}, has_basic_steps: {has_basic_steps}")
    
    if not has_assistant:
        print(f"🎯 ONBOARDING: Missing assistant profile")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot complete onboarding. Assistant profile not created."
        )
    
    if not has_life_areas:
        print(f"🎯 ONBOARDING: Missing life areas")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot complete onboarding. Life areas not selected."
        )
    
    if not has_basic_steps:
        print(f"🎯 ONBOARDING: Insufficient completed steps")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot complete onboarding. Not enough steps completed."
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


@router.post("/reset")
def reset_onboarding(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reset onboarding state to allow user to go through it again."""
    # Get existing onboarding state
    state = db.query(OnboardingState).filter(
        OnboardingState.user_id == current_user["uid"]
    ).first()
    
    if state:
        # Reset onboarding state
        state.current_step = 1
        state.completed_steps = []
        state.onboarding_completed = False
        state.completed_at = None
        state.temp_data = {}
        state.skip_intro = False
        state.last_activity = datetime.utcnow()
        
        # Keep assistant_profile_id, selected_life_areas, first_goal_id, first_task_id
        # so user doesn't lose their existing data
        
        db.commit()
        db.refresh(state)
        
        return {
            "success": True,
            "message": "Onboarding reset successfully. You can now go through the onboarding process again.",
            "current_step": state.current_step,
            "onboarding_completed": state.onboarding_completed
        }
    else:
        # Create new onboarding state if none exists
        state = OnboardingState(
            user_id=current_user["uid"],
            current_step=1,
            completed_steps=[]
        )
        db.add(state)
        db.commit()
        db.refresh(state)
        
        return {
            "success": True,
            "message": "Onboarding state created. You can now go through the onboarding process.",
            "current_step": state.current_step,
            "onboarding_completed": state.onboarding_completed
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
        OnboardingStep.PERSONAL_CONFIG: 5,  # Maps to step 5 (same as LIFE_AREAS)
        OnboardingStep.COMPLETION: 7
    }
    return step_map.get(step, 1)


def _handle_assistant_creation(
    data: Dict[str, Any],
    state: OnboardingState,
    current_user: dict,
    db: Session
) -> Dict[str, Any]:
    """Handle combined assistant creation step (includes personality and language)."""
    # Create the assistant profile directly since we're combining all steps
    from schemas.assistant_schemas import SupportedLanguage
    
    # Get language enum value
    language_code = data.get("language", "en")
    try:
        language = SupportedLanguage(language_code)
    except ValueError:
        language = SupportedLanguage.ENGLISH
    
    # Create or update assistant profile
    existing_assistant = db.query(AssistantProfile).filter(
        AssistantProfile.user_id == state.user_id,
        AssistantProfile.is_default == True
    ).first()
    
    if existing_assistant:
        # Update existing assistant
        existing_assistant.name = data.get("name", "Assistant")
        existing_assistant.avatar_url = data.get("avatar_url")
        existing_assistant.language = language.value
        existing_assistant.requires_confirmation = data.get("requires_confirmation", True)
        existing_assistant.style = data.get("style", {
            "formality": 50,
            "directness": 50,
            "humor": 30,
            "empathy": 70,
            "motivation": 60
        })
        assistant = existing_assistant
    else:
        # Create new assistant
        assistant = AssistantProfile(
            user_id=state.user_id,
            name=data.get("name", "Assistant"),
            avatar_url=data.get("avatar_url"),
            style=data.get("style", {
                "formality": 50,
                "directness": 50,
                "humor": 30,
                "empathy": 70,
                "motivation": 60
            }),
            language=language.value,
            requires_confirmation=data.get("requires_confirmation", True),
            is_default=True
        )
        db.add(assistant)
    
    db.flush()
    state.assistant_profile_id = assistant.id
    
    # No longer using temp_data - all data is stored in proper tables
    
    return {"assistant_id": assistant.id, "assistant_name": data.get("name")}


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
    
    # Style data is now stored directly in AssistantProfile table
    
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
    
    # This step is now handled in _handle_assistant_creation
    # Just return success since assistant is already created
    return {"message": "Language preferences processed - assistant already created"}


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
    
    # Check if user wants to skip goal creation
    if goal_data.skip_goal_creation:
        return {
            "skipped": True,
            "message": "Goal creation skipped. You can create goals, tasks, and projects later from the main dashboard."
        }
    
    # Validate required fields when not skipping
    if not goal_data.title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Goal title is required when not skipping goal creation"
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


def _handle_personal_config(
    data: Dict[str, Any],
    state: OnboardingState,
    current_user: dict,
    db: Session
) -> Dict[str, Any]:
    """Handle personal configuration step - create personal profile and custom life areas."""
    from models import PersonalProfile, CustomLifeArea
    import uuid
    
    try:
        print(f"🔄 ONBOARDING: _handle_personal_config called with data: {data}")
        print(f"🔄 ONBOARDING: User ID: {current_user['uid']}")
        print(f"🔄 ONBOARDING: Custom life areas in data: {data.get('custom_life_areas', [])}")
        # Handle life areas selection (standard life areas)
        life_area_ids = data.get('life_area_ids', [])
        state.selected_life_areas = life_area_ids
        
        # Create personal profile
        profile_data = {
            'current_situation': data.get('current_situation', ''),
            'interests': data.get('interests', []),
            'challenges': data.get('challenges', []),
            'aspirations': data.get('aspirations', ''),
            'preferences': data.get('preferences', {}),
            'custom_answers': data.get('custom_answers', {})
        }
        
        # Check if profile already exists
        existing_profile = db.query(PersonalProfile).filter(
            PersonalProfile.user_id == current_user["uid"]
        ).first()
        
        if existing_profile:
            # Update existing profile
            for field, value in profile_data.items():
                if hasattr(existing_profile, field):
                    setattr(existing_profile, field, value)
            existing_profile.updated_at = datetime.utcnow()
        else:
            # Create new profile
            new_profile = PersonalProfile(
                id=str(uuid.uuid4()),
                user_id=current_user["uid"],
                **profile_data
            )
            db.add(new_profile)
        
        # Create custom life areas if provided
        custom_life_areas = data.get('custom_life_areas', [])
        created_custom_areas = []
        
        if custom_life_areas:
            for area_data in custom_life_areas:
                area_name = area_data.get('name', 'Custom Area').strip()
                
                # Check if this custom life area already exists for this user
                existing_area = db.query(CustomLifeArea).filter(
                    CustomLifeArea.user_id == current_user["uid"],
                    CustomLifeArea.name == area_name
                ).first()
                
                if existing_area:
                    # Area already exists, skip creation
                    created_custom_areas.append(existing_area.id)
                    continue
                
                # Extract icon name from icon data
                icon_name = "category"  # default
                if 'icon_codepoint' in area_data:
                    # Map common icon codepoints to names (simplified mapping)
                    codepoint = area_data.get('icon_codepoint')
                    icon_family = area_data.get('icon_font_family', '')
                    if icon_family == 'MaterialIcons':
                        # You could build a mapping here, for now use category
                        icon_name = "category"
                
                # Convert color value to hex
                color_hex = "#6366f1"  # default
                if 'color_value' in area_data:
                    color_value = area_data.get('color_value')
                    if isinstance(color_value, int):
                        # Convert Flutter color value to hex
                        color_hex = f"#{color_value & 0xFFFFFF:06x}"
                
                custom_area = CustomLifeArea(
                    user_id=current_user["uid"],
                    name=area_name,
                    icon=icon_name,
                    color=color_hex,
                    is_custom=True,
                    priority_order=len(created_custom_areas) + 1
                )
                db.add(custom_area)
                db.flush()
                created_custom_areas.append(custom_area.id)
        
        response_data = {
            "life_area_ids": life_area_ids,
            "custom_life_areas_created": len(created_custom_areas),
            "profile_updated": True
        }
        
        # Handle goal creation if not skipped
        skip_goal = data.get('skip_goal_creation', False)
        if not skip_goal:
            goal_title = data.get('title')
            goal_description = data.get('description', '')
            generate_tasks = data.get('generate_tasks', True)
            
            if goal_title:
                # Create the goal
                goal = Goal(
                    user_id=current_user["uid"],
                    title=goal_title,
                    description=goal_description,
                    status="active",
                    progress_percentage=0
                )
                db.add(goal)
                db.flush()
                
                state.first_goal_id = goal.id
                response_data["goal_id"] = goal.id
                
                # Generate initial task if requested
                if generate_tasks:
                    first_task = Task(
                        user_id=current_user["uid"],
                        goal_id=goal.id,
                        title=f"Get started with: {goal_title}",
                        description="Initial task to begin working on your goal",
                        status="todo",
                        priority="medium"
                    )
                    db.add(first_task)
                    db.flush()
                    
                    state.first_task_id = first_task.id
                    response_data["task_id"] = first_task.id
        
        return response_data
        
    except Exception as e:
        print(f"🔴 ONBOARDING: Error in _handle_personal_config: {str(e)}")
        print(f"🔴 ONBOARDING: Exception type: {type(e)}")
        print(f"🔴 ONBOARDING: Data that caused error: {data}")
        import traceback
        print(f"🔴 ONBOARDING: Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid personal configuration data: {str(e)}"
        )


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