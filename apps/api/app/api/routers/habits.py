from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.models.core import Habit, HabitLog
from ..deps import get_db, get_current_user_id
from ..schemas.habits import HabitCreate, HabitUpdate, HabitOut, HabitLogCreate, HabitLogOut
from ..schemas.common import Page


router = APIRouter(prefix="/habits")


@router.get("/", response_model=Page[HabitOut])
def list_habits(
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    q = db.query(Habit).filter(Habit.user_id == user_id)
    total = q.count()
    items = q.order_by(Habit.created_at.desc()).limit(limit).offset(offset).all()
    return Page[HabitOut](
        total=total,
        items=[HabitOut(id=i.id, title=i.title, schedule_rrule=i.schedule_rrule, cadence_target=i.cadence_target, period=i.period, streak=i.streak) for i in items],
    )


@router.post("/", response_model=HabitOut)
def create_habit(payload: HabitCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    h = Habit(user_id=user_id, title=payload.title, schedule_rrule=payload.schedule_rrule, cadence_target=payload.cadence_target, period=payload.period)
    db.add(h)
    db.commit()
    db.refresh(h)
    return HabitOut(id=h.id, title=h.title, schedule_rrule=h.schedule_rrule, cadence_target=h.cadence_target, period=h.period, streak=h.streak)


@router.patch("/{habit_id}", response_model=HabitOut)
def update_habit(habit_id: str, payload: HabitUpdate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    h = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Habit not found")
    for field in ["title", "schedule_rrule", "cadence_target", "period"]:
        val = getattr(payload, field)
        if val is not None:
            setattr(h, field, val)
    db.commit()
    db.refresh(h)
    return HabitOut(id=h.id, title=h.title, schedule_rrule=h.schedule_rrule, cadence_target=h.cadence_target, period=h.period, streak=h.streak)


@router.get("/{habit_id}/logs", response_model=Page[HabitLogOut])
def list_logs(habit_id: str, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id), limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0)):
    h = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Habit not found")
    q = db.query(HabitLog).filter(HabitLog.habit_id == habit_id)
    total = q.count()
    items = q.order_by(HabitLog.occurred_at.desc()).limit(limit).offset(offset).all()
    return Page[HabitLogOut](
        total=total,
        items=[HabitLogOut(habit_id=i.habit_id, occurred_at=i.occurred_at.isoformat(), value=float(i.value) if i.value is not None else None, note=i.note) for i in items],
    )


@router.post("/{habit_id}/logs", response_model=HabitLogOut)
def add_log(habit_id: str, payload: HabitLogCreate, db: Session = Depends(get_db), user_id: str = Depends(get_current_user_id)):
    h = db.query(Habit).filter(Habit.id == habit_id, Habit.user_id == user_id).first()
    if not h:
        raise HTTPException(status_code=404, detail="Habit not found")
    ts = __import__("datetime").datetime.fromisoformat(payload.occurred_at)
    log = HabitLog(habit_id=habit_id, occurred_at=ts, value=payload.value, note=payload.note)
    db.add(log)
    db.commit()
    return HabitLogOut(habit_id=habit_id, occurred_at=ts.isoformat(), value=payload.value, note=payload.note)

