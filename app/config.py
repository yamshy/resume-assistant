"""Application configuration management."""

from functools import lru_cache
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration values loaded from environment variables."""

    app_env: str = Field(default="development", alias="APP_ENV")
    app_port: int = Field(default=8000, alias="APP_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    database_url: str = Field(
        default="sqlite+aiosqlite:///./resume_tailoring.db",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="memory://", alias="REDIS_URL")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    anthropic_model: str = Field(
        default="claude-3-haiku-20240307", alias="ANTHROPIC_MODEL"
    )

    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    prometheus_enabled: bool = Field(default=True, alias="PROMETHEUS_ENABLED")

    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")
    semantic_cache_ttl: int = Field(default=3600, alias="SEMANTIC_CACHE_TTL")
    semantic_cache_similarity: float = Field(
        default=0.85, alias="SEMANTIC_CACHE_SIMILARITY"
    )
    review_confidence_threshold: float = Field(
        default=0.7, alias="REVIEW_CONFIDENCE_THRESHOLD"
    )
    validation_confidence_threshold: float = Field(
        default=0.8, alias="VALIDATION_CONFIDENCE_THRESHOLD"
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    def to_logging_dict(self) -> dict[str, Any]:
        return {
            "env": self.app_env,
            "database_url": self.database_url,
            "redis_url": self.redis_url,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


__all__ = ["Settings", "get_settings"]
