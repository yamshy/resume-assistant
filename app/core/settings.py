from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    ENV: str = "dev"
    MODEL_NAME: str = "gpt-4o"
    OPENAI_API_KEY: str | None = None

    APP_NAME: str = "Resume Assistant API"
    VERSION: str = "0.1.0"
    DEBUG: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


SettingsDep = Annotated[Settings, Depends(get_settings)]
