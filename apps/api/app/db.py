from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import get_settings


Base = declarative_base()


def get_engine(echo: bool = False):
    settings = get_settings()
    return create_engine(settings.database_url, echo=echo, pool_pre_ping=True, future=True)


def get_session_factory(echo: bool = False):
    engine = get_engine(echo=echo)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

