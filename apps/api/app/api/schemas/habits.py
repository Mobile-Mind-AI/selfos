from pydantic import BaseModel


class HabitCreate(BaseModel):
    title: str
    schedule_rrule: str | None = None
    cadence_target: int | None = None
    period: str | None = None


class HabitUpdate(BaseModel):
    title: str | None = None
    schedule_rrule: str | None = None
    cadence_target: int | None = None
    period: str | None = None


class HabitOut(BaseModel):
    id: str
    title: str
    schedule_rrule: str | None = None
    cadence_target: int | None = None
    period: str | None = None
    streak: int


class HabitLogCreate(BaseModel):
    occurred_at: str
    value: float | None = None
    note: str | None = None


class HabitLogOut(BaseModel):
    habit_id: str
    occurred_at: str
    value: float | None = None
    note: str | None = None

