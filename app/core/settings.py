from functools import lru_cache
from pathlib import Path
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

    STORAGE_BASE_DIR: Path = Path("data")
    PROFILE_STORAGE_PATH: Path | None = None
    RESUME_STORAGE_DIR: Path | None = None

    @property
    def resolved_profile_path(self) -> Path:
        if self.PROFILE_STORAGE_PATH is not None:
            return Path(self.PROFILE_STORAGE_PATH)
        return self.STORAGE_BASE_DIR / "profile.json"

    @property
    def resolved_resumes_dir(self) -> Path:
        if self.RESUME_STORAGE_DIR is not None:
            return Path(self.RESUME_STORAGE_DIR)
        return self.STORAGE_BASE_DIR / "resumes"


@lru_cache
def get_settings() -> Settings:
    return Settings()


SettingsDep = Annotated[Settings, Depends(get_settings)]
