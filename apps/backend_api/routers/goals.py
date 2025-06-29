from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session, joinedload
import models, schemas
from dependencies import get_db, get_current_user

router = APIRouter()

@router.post("/goals", response_model=schemas.GoalOut, status_code=201)
def create_goal(
    goal: schemas.GoalCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    db_goal = models.Goal(
        user_id=current_user["uid"],
        title=goal.title,
        description=goal.description,
        status=goal.status,
        progress=goal.progress,
        life_area_id=goal.life_area_id,
    )
    db.add(db_goal)
    db.commit()
    db.refresh(db_goal)
    return db_goal

@router.get("/goals", response_model=List[schemas.GoalOut])
def list_goals(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return db.query(models.Goal).options(
        joinedload(models.Goal.tasks),
        joinedload(models.Goal.media_attachments),
        joinedload(models.Goal.life_area)
    ).filter(models.Goal.user_id == current_user["uid"]).all()

@router.get("/goals/{goal_id}", response_model=schemas.GoalOut)
def get_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    goal = db.query(models.Goal).options(
        joinedload(models.Goal.tasks),
        joinedload(models.Goal.media_attachments),
        joinedload(models.Goal.life_area)
    ).filter(
        models.Goal.id == goal_id,
        models.Goal.user_id == current_user["uid"]
    ).first()
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
    goal = db.query(models.Goal).options(
        joinedload(models.Goal.tasks),
        joinedload(models.Goal.media_attachments),
        joinedload(models.Goal.life_area)
    ).filter(
        models.Goal.id == goal_id,
        models.Goal.user_id == current_user["uid"]
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    from datetime import datetime
    goal.title = goal_in.title
    goal.description = goal_in.description
    goal.status = goal_in.status
    goal.progress = goal_in.progress
    goal.life_area_id = goal_in.life_area_id
    goal.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(goal)
    return goal

@router.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    goal = db.query(models.Goal).options(
        joinedload(models.Goal.tasks),
        joinedload(models.Goal.media_attachments),
        joinedload(models.Goal.life_area)
    ).filter(
        models.Goal.id == goal_id,
        models.Goal.user_id == current_user["uid"]
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    db.delete(goal)
    db.commit()
    return None