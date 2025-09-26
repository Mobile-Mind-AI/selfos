from functools import lru_cache
from pydantic_settings import BaseSettings


class ApiSettings(BaseSettings):
    app_name: str = "selfos-api"
    allow_origins: list[str] = ["*"]
    fake_user_id: str = "00000000000000000000000000"

    class Config:
        env_prefix = "SELFOS_"


@lru_cache
def get_api_settings() -> ApiSettings:
    return ApiSettings()  # type: ignore

