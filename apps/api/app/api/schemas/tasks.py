from pydantic import BaseModel


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    status: str | None = None
    due_at: str | None = None
    rrule: str | None = None
    effort_minutes: int | None = None
    goal_id: str | None = None
    project_id: str | None = None
    habit_id: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    due_at: str | None = None
    rrule: str | None = None
    effort_minutes: int | None = None
    goal_id: str | None = None
    project_id: str | None = None
    habit_id: str | None = None


class TaskOut(BaseModel):
    id: str
    title: str
    description: str | None = None
    status: str
    due_at: str | None = None
    rrule: str | None = None
    effort_minutes: int | None = None
    goal_id: str | None = None
    project_id: str | None = None
    habit_id: str | None = None

