from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.core import Project
from ..deps import get_db, get_current_user_id
from ..schemas.projects import ProjectCreate, ProjectUpdate, ProjectOut
from ..schemas.common import Page


router = APIRouter(prefix="/projects")


@router.get("/", response_model=Page[ProjectOut])
def list_projects(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    q = db.query(Project).filter(Project.user_id == user_id)
    total = q.count()
    items = q.order_by(Project.created_at.desc()).limit(limit).offset(offset).all()
    return Page[ProjectOut](
        total=total,
        items=[ProjectOut(id=i.id, title=i.title, description=i.description, status=i.status) for i in items],
    )


@router.post("/", response_model=ProjectOut)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    p = Project(user_id=user_id, title=payload.title, description=payload.description, status=payload.status or "active")
    db.add(p)
    db.commit()
    db.refresh(p)
    return ProjectOut(id=p.id, title=p.title, description=p.description, status=p.status)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    p = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectOut(id=p.id, title=p.title, description=p.description, status=p.status)


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(project_id: str, payload: ProjectUpdate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    p = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    for field in ["title", "description", "status"]:
        val = getattr(payload, field)
        if val is not None:
            setattr(p, field, val)
    db.commit()
    db.refresh(p)
    return ProjectOut(id=p.id, title=p.title, description=p.description, status=p.status)


@router.delete("/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    p = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(p)
    db.commit()
    return {"ok": True}

