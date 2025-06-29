from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session, joinedload
import models, schemas
from dependencies import get_db, get_current_user
from event_bus import publish_task_completed, EventType, publish

router = APIRouter()

@router.post("/tasks", response_model=schemas.TaskOut, status_code=201)
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    db_task = models.Task(
        goal_id=task.goal_id,
        user_id=current_user["uid"],
        title=task.title,
        description=task.description,
        due_date=task.due_date,
        duration=task.duration,
        status=task.status,
        progress=task.progress,
        life_area_id=task.life_area_id,
        dependencies=task.dependencies,
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.get("/tasks", response_model=List[schemas.TaskOut])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return db.query(models.Task).options(
        joinedload(models.Task.media_attachments),
        joinedload(models.Task.life_area)
    ).filter(models.Task.user_id == current_user["uid"]).all()

@router.get("/tasks/{task_id}", response_model=schemas.TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    task = db.query(models.Task).options(
        joinedload(models.Task.media_attachments),
        joinedload(models.Task.life_area)
    ).filter(
        models.Task.id == task_id,
        models.Task.user_id == current_user["uid"]
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.put("/tasks/{task_id}", response_model=schemas.TaskOut)
async def update_task(
    task_id: int,
    task_in: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    task = db.query(models.Task).options(
        joinedload(models.Task.media_attachments),
        joinedload(models.Task.life_area)
    ).filter(
        models.Task.id == task_id,
        models.Task.user_id == current_user["uid"]
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    from datetime import datetime
    
    # Store old status to detect completion
    old_status = task.status
    
    # Update task fields
    task.title = task_in.title
    task.description = task_in.description
    task.due_date = task_in.due_date
    task.duration = task_in.duration
    task.status = task_in.status
    task.progress = task_in.progress
    task.life_area_id = task_in.life_area_id
    task.dependencies = task_in.dependencies
    task.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(task)
    
    # Publish event if task was just completed
    if old_status != "completed" and task.status == "completed":
        await publish_task_completed(
            task_id=str(task.id),
            user_id=task.user_id,
            task_data={
                "title": task.title,
                "description": task.description,
                "goal_id": str(task.goal_id),
                "life_area_id": str(task.life_area_id) if task.life_area_id else None,
                "duration": task.duration,
                "media_count": len(task.media_attachments) if task.media_attachments else 0
            }
        )
    
    return task

@router.put("/tasks/{task_id}/complete", response_model=schemas.TaskOut)
async def mark_task_complete(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Mark a task as completed and trigger AI processing events."""
    task = db.query(models.Task).options(
        joinedload(models.Task.media_attachments),
        joinedload(models.Task.life_area)
    ).filter(
        models.Task.id == task_id,
        models.Task.user_id == current_user["uid"]
    ).first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status == "completed":
        raise HTTPException(status_code=400, detail="Task is already completed")
    
    from datetime import datetime
    
    # Mark as completed
    old_status = task.status
    task.status = "completed"
    task.progress = 100.0
    task.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(task)
    
    # Publish completion event
    await publish_task_completed(
        task_id=str(task.id),
        user_id=task.user_id,
        task_data={
            "title": task.title,
            "description": task.description,
            "goal_id": str(task.goal_id),
            "life_area_id": str(task.life_area_id) if task.life_area_id else None,
            "duration": task.duration,
            "media_count": len(task.media_attachments) if task.media_attachments else 0,
            "previous_status": old_status
        }
    )
    
    return task

@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == current_user["uid"]
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return None