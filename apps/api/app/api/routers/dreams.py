from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.core import Dream
from ..deps import get_db, get_current_user_id
from ..schemas.dreams import DreamCreate, DreamUpdate, DreamOut
from ..schemas.common import Page


router = APIRouter(prefix="/dreams")


@router.get("/", response_model=Page[DreamOut])
def list_dreams(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    q = db.query(Dream).filter(Dream.user_id == user_id)
    total = q.count()
    items = q.order_by(Dream.created_at.desc()).limit(limit).offset(offset).all()
    return Page[DreamOut](
        total=total,
        items=[DreamOut(id=i.id, title=i.title, description=i.description, status=i.status, horizon=i.horizon) for i in items],
    )


@router.post("/", response_model=DreamOut)
def create_dream(payload: DreamCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    d = Dream(user_id=user_id, title=payload.title, description=payload.description, status=payload.status or "incubating", horizon=payload.horizon)
    db.add(d)
    db.commit()
    db.refresh(d)
    return DreamOut(id=d.id, title=d.title, description=d.description, status=d.status, horizon=d.horizon)


@router.get("/{dream_id}", response_model=DreamOut)
def get_dream(dream_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    d = db.query(Dream).filter(Dream.id == dream_id, Dream.user_id == user_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dream not found")
    return DreamOut(id=d.id, title=d.title, description=d.description, status=d.status, horizon=d.horizon)


@router.patch("/{dream_id}", response_model=DreamOut)
def update_dream(dream_id: str, payload: DreamUpdate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    d = db.query(Dream).filter(Dream.id == dream_id, Dream.user_id == user_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dream not found")
    for field in ["title", "description", "status", "horizon"]:
        val = getattr(payload, field)
        if val is not None:
            setattr(d, field, val)
    db.commit()
    db.refresh(d)
    return DreamOut(id=d.id, title=d.title, description=d.description, status=d.status, horizon=d.horizon)


@router.delete("/{dream_id}")
def delete_dream(dream_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    d = db.query(Dream).filter(Dream.id == dream_id, Dream.user_id == user_id).first()
    if not d:
        raise HTTPException(status_code=404, detail="Dream not found")
    db.delete(d)
    db.commit()
    return {"ok": True}

