from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.core import Goal
from ..deps import get_db, get_current_user_id
from ..schemas.goals import GoalCreate, GoalUpdate, GoalOut
from ..schemas.common import Page


router = APIRouter(prefix="/goals")


@router.get("/", response_model=Page[GoalOut])
def list_goals(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    q = db.query(Goal).filter(Goal.user_id == user_id)
    total = q.count()
    items = q.order_by(Goal.created_at.desc()).limit(limit).offset(offset).all()
    return Page[GoalOut](
        total=total,
        items=[GoalOut(
            id=i.id,
            title=i.title,
            description=i.description,
            target_date=i.target_date.isoformat() if i.target_date else None,
            status=i.status,
            dream_id=i.dream_id,
            project_id=i.project_id,
        ) for i in items],
    )


@router.post("/", response_model=GoalOut)
def create_goal(payload: GoalCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    g = Goal(
        user_id=user_id,
        title=payload.title,
        description=payload.description,
        target_date=None if not payload.target_date else __import__("datetime").datetime.fromisoformat(payload.target_date),
        status=payload.status or "active",
        dream_id=payload.dream_id,
        project_id=payload.project_id,
    )
    db.add(g)
    db.commit()
    db.refresh(g)
    return GoalOut(
        id=g.id,
        title=g.title,
        description=g.description,
        target_date=g.target_date.isoformat() if g.target_date else None,
        status=g.status,
        dream_id=g.dream_id,
        project_id=g.project_id,
    )


@router.get("/{goal_id}", response_model=GoalOut)
def get_goal(goal_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    g = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Goal not found")
    return GoalOut(
        id=g.id, title=g.title, description=g.description,
        target_date=g.target_date.isoformat() if g.target_date else None,
        status=g.status, dream_id=g.dream_id, project_id=g.project_id,
    )


@router.patch("/{goal_id}", response_model=GoalOut)
def update_goal(goal_id: str, payload: GoalUpdate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    g = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Goal not found")
    if payload.title is not None:
        g.title = payload.title
    if payload.description is not None:
        g.description = payload.description
    if payload.status is not None:
        g.status = payload.status
    if payload.dream_id is not None:
        g.dream_id = payload.dream_id
    if payload.project_id is not None:
        g.project_id = payload.project_id
    if payload.target_date is not None:
        g.target_date = __import__("datetime").datetime.fromisoformat(payload.target_date) if payload.target_date else None
    db.commit()
    db.refresh(g)
    return GoalOut(
        id=g.id, title=g.title, description=g.description,
        target_date=g.target_date.isoformat() if g.target_date else None,
        status=g.status, dream_id=g.dream_id, project_id=g.project_id,
    )


@router.delete("/{goal_id}")
def delete_goal(goal_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    g = db.query(Goal).filter(Goal.id == goal_id, Goal.user_id == user_id).first()
    if not g:
        raise HTTPException(status_code=404, detail="Goal not found")
    db.delete(g)
    db.commit()
    return {"ok": True}

