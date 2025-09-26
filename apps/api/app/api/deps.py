from typing import Iterator
from sqlalchemy.orm import Session

from ..db import get_session_factory
from .settings import get_api_settings


def get_db() -> Iterator[Session]:
    SessionFactory = get_session_factory()
    db = SessionFactory()
    try:
        yield db
    finally:
        db.close()


def get_current_user_id() -> str:
    # Placeholder auth: return fixed user id from settings
    return get_api_settings().fake_user_id

