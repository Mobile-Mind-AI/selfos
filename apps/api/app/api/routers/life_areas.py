from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.core import LifeArea
from ..deps import get_db, get_current_user_id
from ..schemas.life_areas import LifeAreaCreate, LifeAreaUpdate, LifeAreaOut
from ..schemas.common import Page


router = APIRouter(prefix="/life-areas")


@router.get("/", response_model=Page[LifeAreaOut])
def list_life_areas(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    q = db.query(LifeArea).filter(LifeArea.user_id == user_id)
    total = q.count()
    items = q.order_by(LifeArea.created_at.desc()).limit(limit).offset(offset).all()
    return Page[LifeAreaOut](
        total=total,
        items=[LifeAreaOut(id=i.id, name=i.name, color=i.color) for i in items],
    )


@router.post("/", response_model=LifeAreaOut)
def create_life_area(payload: LifeAreaCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    la = LifeArea(user_id=user_id, name=payload.name, color=payload.color)
    db.add(la)
    db.commit()
    db.refresh(la)
    return LifeAreaOut(id=la.id, name=la.name, color=la.color)


@router.patch("/{life_area_id}", response_model=LifeAreaOut)
def update_life_area(life_area_id: str, payload: LifeAreaUpdate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    la = db.query(LifeArea).filter(LifeArea.id == life_area_id, LifeArea.user_id == user_id).first()
    if not la:
        raise HTTPException(status_code=404, detail="Life area not found")
    if payload.name is not None:
        la.name = payload.name
    if payload.color is not None:
        la.color = payload.color
    db.commit()
    db.refresh(la)
    return LifeAreaOut(id=la.id, name=la.name, color=la.color)


@router.delete("/{life_area_id}")
def delete_life_area(life_area_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    la = db.query(LifeArea).filter(LifeArea.id == life_area_id, LifeArea.user_id == user_id).first()
    if not la:
        raise HTTPException(status_code=404, detail="Life area not found")
    db.delete(la)
    db.commit()
    return {"ok": True}

