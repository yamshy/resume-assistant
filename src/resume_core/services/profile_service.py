from __future__ import annotations

from pathlib import Path
from typing import Any

from resume_core.models.profile import UserProfile
from resume_core.services.storage_service import StorageService


class ProfileService:
    def __init__(
        self,
        storage_service: StorageService | None = None,
        *,
        base_path: Path | str | None = None,
    ) -> None:
        self.storage = storage_service or StorageService(base_path=base_path)

    def load_profile(self) -> UserProfile:
        data = self.storage.load_profile()
        if not data:
            return UserProfile.empty()
        return UserProfile.model_validate(data)

    def save_profile(self, profile: UserProfile | dict[str, Any]) -> UserProfile:
        if not isinstance(profile, UserProfile):
            profile = UserProfile.model_validate(profile)
        self.storage.save_profile(profile.model_dump())
        return profile

    def update_profile(self, payload: dict[str, Any]) -> UserProfile:
        current = self.load_profile()
        updated = current.merge_overrides(payload)
        self.storage.save_profile(updated.model_dump())
        return updated
