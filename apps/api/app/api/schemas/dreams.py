from pydantic import BaseModel


class DreamCreate(BaseModel):
    title: str
    description: str | None = None
    status: str | None = None
    horizon: str | None = None


class DreamUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    horizon: str | None = None


class DreamOut(BaseModel):
    id: str
    title: str
    description: str | None = None
    status: str | None = None
    horizon: str | None = None

