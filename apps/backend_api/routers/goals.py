from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
import schemas
from dependencies import get_db, get_current_user
from services.goal_service import goal_service

router = APIRouter(
    prefix="/goals",
    tags=["goals"],
    dependencies=[Depends(get_current_user)]
)


@router.post("/", response_model=schemas.GoalOut, status_code=201)
def create_goal(
    goal: schemas.GoalCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new goal for the current user."""
    return goal_service.create_goal(db, current_user["uid"], goal)


@router.get("/", response_model=List[schemas.GoalOut])
def list_goals(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all goals for the current user."""
    return goal_service.list_goals(db, current_user["uid"])


# Hierarchy endpoints - MUST come before /{goal_id} to avoid route conflicts
@router.get("/roots", response_model=List[schemas.GoalOut])
def get_root_goals(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all root-level goals (goals without parents)."""
    return goal_service.get_root_goals(db, current_user["uid"])


@router.get("/tree", response_model=List[schemas.HierarchyTreeNode])
def get_goal_tree(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get hierarchical tree structure of all goals."""
    return goal_service.get_goal_tree(db, current_user["uid"])


@router.get("/life-area/{life_area_id}", response_model=List[schemas.GoalOut])
def get_goals_by_life_area(
    life_area_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all goals for a specific life area."""
    return goal_service.get_goals_by_life_area(db, current_user["uid"], life_area_id)


@router.get("/status/{status}", response_model=List[schemas.GoalOut])
def get_goals_by_status(
    status: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all goals with a specific status."""
    return goal_service.get_goals_by_status(db, current_user["uid"], status)


# Single goal endpoints - MUST come after specific routes
@router.get("/{goal_id}", response_model=schemas.GoalOut)
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


@router.get("/{goal_id}/children", response_model=List[schemas.GoalOut])
def get_goal_children(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get direct children of a goal."""
    # Verify goal exists and user has access
    goal = goal_service.get_goal(db, current_user["uid"], goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    return goal_service.get_goal_children(db, current_user["uid"], goal_id)


@router.get("/{goal_id}/descendants", response_model=List[schemas.GoalOut])
def get_goal_descendants(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all descendants (children, grandchildren, etc.) of a goal."""
    # Verify goal exists and user has access
    goal = goal_service.get_goal(db, current_user["uid"], goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    return goal_service.get_goal_descendants(db, current_user["uid"], goal_id)


@router.get("/{goal_id}/path", response_model=List[schemas.HierarchyPathItem])
def get_goal_path(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get the full path from root to the specified goal."""
    # Verify goal exists and user has access
    goal = goal_service.get_goal(db, current_user["uid"], goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    
    return goal_service.get_goal_path(db, current_user["uid"], goal_id)


@router.put("/{goal_id}", response_model=schemas.GoalOut)
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


@router.put("/{goal_id}/move", response_model=schemas.GoalOut)
def move_goal(
    goal_id: int,
    move_request: schemas.HierarchyMoveRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Move a goal to a new parent in the hierarchy."""
    try:
        goal = goal_service.move_goal(db, current_user["uid"], goal_id, move_request.parent_id)
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        return goal
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
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
