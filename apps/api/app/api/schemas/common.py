from typing import Generic, TypeVar, List
from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    total: int
    items: List[T]

