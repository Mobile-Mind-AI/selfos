
import schemas
from dependencies import get_current_user, get_db
from fastapi import APIRouter, Depends, HTTPException, status
from services.task_service import task_service
from sqlalchemy.orm import Session

router = APIRouter()


@router.post("/tasks", response_model=schemas.TaskOut, status_code=201)
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Create a new task for the current user."""
    return task_service.create_task(db, current_user["uid"], task)


@router.get("/tasks", response_model=list[schemas.TaskOut])
def list_tasks(
    db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    """List all tasks for the current user."""
    return task_service.list_tasks(db, current_user["uid"])


@router.get("/tasks/{task_id}", response_model=schemas.TaskOut)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get a specific task by ID."""
    task = task_service.get_task(db, current_user["uid"], task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/tasks/{task_id}", response_model=schemas.TaskOut)
async def update_task(
    task_id: int,
    task_in: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Update an existing task."""
    task = await task_service.update_task(db, current_user["uid"], task_id, task_in)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/tasks/{task_id}/complete", response_model=schemas.TaskOut)
async def mark_task_complete(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Mark a task as completed and trigger AI processing events."""
    task = await task_service.mark_task_complete(db, current_user["uid"], task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Check if task was already completed (TaskService handles this gracefully)
    if task.status != "completed":
        raise HTTPException(status_code=400, detail="Unable to complete task")

    return task


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a task."""
    success = task_service.delete_task(db, current_user["uid"], task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return None


@router.get("/tasks/goal/{goal_id}", response_model=list[schemas.TaskOut])
def get_tasks_by_goal(
    goal_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get all tasks for a specific goal."""
    return task_service.get_tasks_by_goal(db, current_user["uid"], goal_id)


@router.get("/tasks/status/{status}", response_model=list[schemas.TaskOut])
def get_tasks_by_status(
    status: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get all tasks with a specific status."""
    return task_service.get_tasks_by_status(db, current_user["uid"], status)
