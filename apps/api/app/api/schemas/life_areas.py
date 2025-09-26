from pydantic import BaseModel


class LifeAreaCreate(BaseModel):
    name: str
    color: str | None = None


class LifeAreaUpdate(BaseModel):
    name: str | None = None
    color: str | None = None


class LifeAreaOut(BaseModel):
    id: str
    name: str
    color: str | None = None

