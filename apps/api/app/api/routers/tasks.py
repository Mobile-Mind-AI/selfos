from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.core import Task
from ..deps import get_db, get_current_user_id
from ..schemas.tasks import TaskCreate, TaskUpdate, TaskOut
from ..schemas.common import Page


router = APIRouter(prefix="/tasks")


@router.get("/", response_model=Page[TaskOut])
def list_tasks(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: str | None = None,
):
    q = db.query(Task).filter(Task.user_id == user_id)
    if status:
        q = q.filter(Task.status == status)
    total = q.count()
    items = q.order_by(Task.created_at.desc()).limit(limit).offset(offset).all()
    return Page[TaskOut](
        total=total,
        items=[TaskOut(
            id=i.id, title=i.title, description=i.description, status=i.status,
            due_at=i.due_at.isoformat() if i.due_at else None,
            rrule=i.rrule, effort_minutes=i.effort_minutes,
            goal_id=i.goal_id, project_id=i.project_id, habit_id=i.habit_id,
        ) for i in items],
    )


@router.post("/", response_model=TaskOut)
def create_task(payload: TaskCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    due = __import__("datetime").datetime.fromisoformat(payload.due_at) if payload.due_at else None
    t = Task(
        user_id=user_id, title=payload.title, description=payload.description,
        status=payload.status or "pending", due_at=due, rrule=payload.rrule,
        effort_minutes=payload.effort_minutes, goal_id=payload.goal_id,
        project_id=payload.project_id, habit_id=payload.habit_id,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return TaskOut(
        id=t.id, title=t.title, description=t.description, status=t.status,
        due_at=t.due_at.isoformat() if t.due_at else None,
        rrule=t.rrule, effort_minutes=t.effort_minutes,
        goal_id=t.goal_id, project_id=t.project_id, habit_id=t.habit_id,
    )


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    t = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskOut(
        id=t.id, title=t.title, description=t.description, status=t.status,
        due_at=t.due_at.isoformat() if t.due_at else None, rrule=t.rrule,
        effort_minutes=t.effort_minutes, goal_id=t.goal_id, project_id=t.project_id, habit_id=t.habit_id,
    )


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: str, payload: TaskUpdate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    t = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    if payload.title is not None:
        t.title = payload.title
    if payload.description is not None:
        t.description = payload.description
    if payload.status is not None:
        t.status = payload.status
    if payload.due_at is not None:
        t.due_at = __import__("datetime").datetime.fromisoformat(payload.due_at) if payload.due_at else None
    if payload.rrule is not None:
        t.rrule = payload.rrule
    if payload.effort_minutes is not None:
        t.effort_minutes = payload.effort_minutes
    if payload.goal_id is not None:
        t.goal_id = payload.goal_id
    if payload.project_id is not None:
        t.project_id = payload.project_id
    if payload.habit_id is not None:
        t.habit_id = payload.habit_id
    db.commit()
    db.refresh(t)
    return TaskOut(
        id=t.id, title=t.title, description=t.description, status=t.status,
        due_at=t.due_at.isoformat() if t.due_at else None, rrule=t.rrule,
        effort_minutes=t.effort_minutes, goal_id=t.goal_id, project_id=t.project_id, habit_id=t.habit_id,
    )


@router.delete("/{task_id}")
def delete_task(task_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    t = db.query(Task).filter(Task.id == task_id, Task.user_id == user_id).first()
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(t)
    db.commit()
    return {"ok": True}

