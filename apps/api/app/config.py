from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "selfos-api"
    database_url: str = "postgresql+psycopg://user:pass@localhost:5432/selfos_dev"
    pgvector_dimension: int = 1536

    class Config:
        env_prefix = "SELFOS_"
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]

