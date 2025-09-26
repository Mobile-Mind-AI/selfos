from pydantic import BaseModel


class ProjectCreate(BaseModel):
    title: str
    description: str | None = None
    status: str | None = None


class ProjectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None


class ProjectOut(BaseModel):
    id: str
    title: str
    description: str | None = None
    status: str | None = None

