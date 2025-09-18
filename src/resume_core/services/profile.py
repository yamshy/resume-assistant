from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from resume_core.models.profile import UserProfile


class ProfileStore:
    """File-backed storage for the single user profile."""

    def __init__(self, base_path: Path | str | None = None) -> None:
        if base_path is None:
            env_dir = os.environ.get("RESUME_ASSISTANT_DATA_DIR")
            if env_dir:
                base_path = Path(env_dir)
            else:
                base_path = Path.home() / ".resume-assistant"
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._profile_path = self.base_path / "profile.json"
        self._adapter: TypeAdapter[UserProfile] = TypeAdapter(UserProfile)

    @property
    def profile_path(self) -> Path:
        return self._profile_path

    def get_profile(self) -> UserProfile | None:
        if not self._profile_path.exists():
            return None
        data = json.loads(self._profile_path.read_text(encoding="utf-8"))
        return self._adapter.validate_python(data)

    def save_profile(self, profile: UserProfile | dict[str, Any]) -> UserProfile:
        profile_model = self._adapter.validate_python(profile)
        self._profile_path.write_text(
            profile_model.model_dump_json(indent=2, exclude_none=True),
            encoding="utf-8",
        )
        return profile_model

