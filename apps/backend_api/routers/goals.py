from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
import schemas
from dependencies import get_db, get_current_user
from services.goal_service import goal_service

router = APIRouter()


@router.post("/goals", response_model=schemas.GoalOut, status_code=201)
def create_goal(
    goal: schemas.GoalCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new goal for the current user."""
    return goal_service.create_goal(db, current_user["uid"], goal)


@router.get("/goals", response_model=List[schemas.GoalOut])
def list_goals(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all goals for the current user."""
    return goal_service.list_goals(db, current_user["uid"])


@router.get("/goals/{goal_id}", response_model=schemas.GoalOut)
def get_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific goal by ID."""
    goal = goal_service.get_goal(db, current_user["uid"], goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.put("/goals/{goal_id}", response_model=schemas.GoalOut)
def update_goal(
    goal_id: int,
    goal_in: schemas.GoalCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an existing goal."""
    goal = goal_service.update_goal(db, current_user["uid"], goal_id, goal_in)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return goal


@router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a goal."""
    success = goal_service.delete_goal(db, current_user["uid"], goal_id)
    if not success:
        raise HTTPException(status_code=404, detail="Goal not found")
    return None


@router.get("/goals/life-area/{life_area_id}", response_model=List[schemas.GoalOut])
def get_goals_by_life_area(
    life_area_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all goals for a specific life area."""
    return goal_service.get_goals_by_life_area(db, current_user["uid"], life_area_id)


@router.get("/goals/status/{status}", response_model=List[schemas.GoalOut])
def get_goals_by_status(
    status: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all goals with a specific status."""
    return goal_service.get_goals_by_status(db, current_user["uid"], status)
