from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from resume_core.models.profile import UserProfile

from .storage_service import StorageService


class ProfileService:
    def __init__(self, storage: StorageService, profile_path: Path | None = None) -> None:
        self.storage = storage
        self.profile_path = profile_path or Path("profile.json")

    async def load_profile(self) -> UserProfile | None:
        data = await self.storage.read_json(self.profile_path)
        if data is None:
            return None
        return UserProfile.model_validate(data)

    async def save_profile(self, profile: UserProfile) -> UserProfile:
        now = datetime.now(timezone.utc)
        profile.metadata.updated_at = now
        # Preserve the original creation timestamp if present, otherwise initialize it.
        if profile.metadata.created_at is None:
            profile.metadata.created_at = now

        await self.storage.write_json(self.profile_path, profile.model_dump(mode="json"))
        return profile
