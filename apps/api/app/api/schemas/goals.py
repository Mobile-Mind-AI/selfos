from pydantic import BaseModel


class GoalCreate(BaseModel):
    title: str
    description: str | None = None
    target_date: str | None = None
    status: str | None = None
    dream_id: str | None = None
    project_id: str | None = None


class GoalUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    target_date: str | None = None
    status: str | None = None
    dream_id: str | None = None
    project_id: str | None = None


class GoalOut(BaseModel):
    id: str
    title: str
    description: str | None = None
    target_date: str | None = None
    status: str | None = None
    dream_id: str | None = None
    project_id: str | None = None

