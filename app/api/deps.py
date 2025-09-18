from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from app.core.settings import SettingsDep
from resume_core.services import ProfileStore, ResumeTailoringService


def _default_data_dir() -> Path:
    env_dir = os.environ.get("RESUME_ASSISTANT_DATA_DIR")
    if env_dir:
        return Path(env_dir)
    return Path.home() / ".resume-assistant"


@lru_cache
def _build_service(data_dir: str | None) -> ResumeTailoringService:
    base_path = Path(data_dir) if data_dir else _default_data_dir()
    store = ProfileStore(base_path=base_path)
    return ResumeTailoringService(profile_store=store)


def get_tailoring_service(settings: SettingsDep) -> ResumeTailoringService:
    return _build_service(settings.DATA_DIR)

