"""
Habits Router

This router handles all HTTP endpoints related to habit management,
including CRUD operations, completion tracking, and progress monitoring.
"""

from datetime import date, timedelta

import models
import schemas
from dependencies import get_current_user, get_db
from fastapi import APIRouter, Depends, HTTPException, Query, status
from services.habit_service import habit_service
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/habits", response_model=schemas.HabitOut, status_code=201)
def create_habit(
    habit: schemas.HabitCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new habit for the current user."""
    return habit_service.create_habit(db, current_user["uid"], habit)


@router.get("/habits", response_model=list[schemas.HabitOut])
def list_habits(
    is_active: bool | None = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all habits for the current user."""
    habits = habit_service.list_habits(db, current_user["uid"], is_active)

    # Enrich each habit with current period progress
    enriched_habits = []
    for habit in habits:
        # Convert to dict to avoid SQLAlchemy issues
        habit_dict = {
            "id": habit.id,
            "user_id": habit.user_id,
            "title": habit.title,
            "description": habit.description,
            "recurrence_rule": habit.recurrence_rule,
            "is_active": habit.is_active,
            "start_date": habit.start_date,
            "end_date": habit.end_date,
            "icon": habit.icon,
            "color": habit.color,
            "goal_id": habit.goal_id,
            "life_area_id": habit.life_area_id,
            "current_streak": habit.current_streak,
            "best_streak": habit.best_streak,
            "total_completions": habit.total_completions,
            "created_at": habit.created_at,
            "updated_at": habit.updated_at,
        }

        # Add current period progress
        progress = habit_service.get_habit_progress(db, current_user["uid"], habit.id)
        habit_dict["current_period_progress"] = progress

        # Add recent completions (last 7 days)
        recent_completions = habit_service.get_habit_completions(
            db,
            current_user["uid"],
            habit.id,
            start_date=date.today() - timedelta(days=7),
        )
        habit_dict["recent_completions"] = recent_completions

        # Add related objects
        habit_dict["goal"] = habit.goal
        habit_dict["life_area"] = habit.life_area

        enriched_habits.append(schemas.HabitOut(**habit_dict))

    return enriched_habits


@router.get("/habits/{habit_id}", response_model=schemas.HabitOut)
def get_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a specific habit by ID with current progress and recent completions."""
    habit = habit_service.get_habit(db, current_user["uid"], habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    # Convert to dict and enrich with progress data
    habit_dict = {
        "id": habit.id,
        "user_id": habit.user_id,
        "title": habit.title,
        "description": habit.description,
        "recurrence_rule": habit.recurrence_rule,
        "is_active": habit.is_active,
        "start_date": habit.start_date,
        "end_date": habit.end_date,
        "icon": habit.icon,
        "color": habit.color,
        "goal_id": habit.goal_id,
        "life_area_id": habit.life_area_id,
        "current_streak": habit.current_streak,
        "best_streak": habit.best_streak,
        "total_completions": habit.total_completions,
        "created_at": habit.created_at,
        "updated_at": habit.updated_at,
    }

    # Add current period progress
    progress = habit_service.get_habit_progress(db, current_user["uid"], habit_id)
    habit_dict["current_period_progress"] = progress

    # Add recent completions (last 30 days)
    from datetime import timedelta

    recent_completions = habit_service.get_habit_completions(
        db, current_user["uid"], habit_id, start_date=date.today() - timedelta(days=30)
    )
    habit_dict["recent_completions"] = recent_completions

    # Add related objects
    habit_dict["goal"] = habit.goal
    habit_dict["life_area"] = habit.life_area

    return schemas.HabitOut(**habit_dict)


@router.put("/habits/{habit_id}", response_model=schemas.HabitOut)
def update_habit(
    habit_id: int,
    habit_in: schemas.HabitUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update an existing habit."""
    habit = habit_service.update_habit(db, current_user["uid"], habit_id, habit_in)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    # Convert and enrich similar to get_habit
    habit_dict = {
        "id": habit.id,
        "user_id": habit.user_id,
        "title": habit.title,
        "description": habit.description,
        "recurrence_rule": habit.recurrence_rule,
        "is_active": habit.is_active,
        "start_date": habit.start_date,
        "end_date": habit.end_date,
        "icon": habit.icon,
        "color": habit.color,
        "goal_id": habit.goal_id,
        "life_area_id": habit.life_area_id,
        "current_streak": habit.current_streak,
        "best_streak": habit.best_streak,
        "total_completions": habit.total_completions,
        "created_at": habit.created_at,
        "updated_at": habit.updated_at,
    }

    progress = habit_service.get_habit_progress(db, current_user["uid"], habit_id)
    habit_dict["current_period_progress"] = progress

    from datetime import timedelta

    recent_completions = habit_service.get_habit_completions(
        db, current_user["uid"], habit_id, start_date=date.today() - timedelta(days=7)
    )
    habit_dict["recent_completions"] = recent_completions

    habit_dict["goal"] = habit.goal
    habit_dict["life_area"] = habit.life_area

    return schemas.HabitOut(**habit_dict)


@router.delete("/habits/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_habit(
    habit_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a habit and all its completions."""
    success = habit_service.delete_habit(db, current_user["uid"], habit_id)
    if not success:
        raise HTTPException(status_code=404, detail="Habit not found")
    return None


@router.post(
    "/habits/{habit_id}/complete",
    response_model=schemas.HabitCompletion,
    status_code=201,
)
def complete_habit(
    habit_id: int,
    completion: schemas.HabitCompletionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Record a completion of a habit."""
    completion_record = habit_service.complete_habit(
        db, current_user["uid"], habit_id, completion
    )
    if not completion_record:
        raise HTTPException(status_code=404, detail="Active habit not found")
    return completion_record


@router.get(
    "/habits/{habit_id}/completions", response_model=list[schemas.HabitCompletion]
)
def get_habit_completions(
    habit_id: int,
    start_date: date | None = Query(
        None, description="Start date for completion range"
    ),
    end_date: date | None = Query(None, description="End date for completion range"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get completions for a habit within a date range."""
    completions = habit_service.get_habit_completions(
        db, current_user["uid"], habit_id, start_date, end_date
    )
    return completions


@router.get("/habits/{habit_id}/progress", response_model=schemas.HabitProgress)
def get_habit_progress(
    habit_id: int,
    target_date: date | None = Query(
        None, description="Date to calculate progress for (defaults to today)"
    ),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get progress for a habit for the current period."""
    progress = habit_service.get_habit_progress(
        db, current_user["uid"], habit_id, target_date
    )
    if not progress:
        raise HTTPException(status_code=404, detail="Habit not found")
    return progress


@router.put(
    "/habits/{habit_id}/completions/{completion_id}",
    response_model=schemas.HabitCompletion,
)
def update_completion(
    habit_id: int,
    completion_id: int,
    completion_data: schemas.HabitCompletionUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update a habit completion (notes, duration, intensity)."""
    # First verify the habit belongs to the user
    habit = habit_service.get_habit(db, current_user["uid"], habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    # Get the completion
    completion = (
        db.query(models.HabitCompletion)
        .filter(
            models.HabitCompletion.id == completion_id,
            models.HabitCompletion.habit_id == habit_id,
        )
        .first()
    )

    if not completion:
        raise HTTPException(status_code=404, detail="Completion not found")

    # Update fields
    update_fields = completion_data.dict(exclude_unset=True)
    for field, value in update_fields.items():
        setattr(completion, field, value)

    db.commit()
    db.refresh(completion)

    return completion


@router.delete(
    "/habits/{habit_id}/completions/{completion_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_completion(
    habit_id: int,
    completion_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a habit completion."""
    # First verify the habit belongs to the user
    habit = habit_service.get_habit(db, current_user["uid"], habit_id)
    if not habit:
        raise HTTPException(status_code=404, detail="Habit not found")

    # Get the completion
    completion = (
        db.query(models.HabitCompletion)
        .filter(
            models.HabitCompletion.id == completion_id,
            models.HabitCompletion.habit_id == habit_id,
        )
        .first()
    )

    if not completion:
        raise HTTPException(status_code=404, detail="Completion not found")

    # Store completion date for stats recalculation

    # Delete completion
    db.delete(completion)

    # Recalculate habit stats
    habit.total_completions = max(0, habit.total_completions - 1)

    # Recalculate streaks (simple approach - could be optimized)
    from services.habit_service import habit_service as hs

    habit.current_streak = hs._calculate_current_streak(db, habit_id, date.today())

    db.commit()

    return None
