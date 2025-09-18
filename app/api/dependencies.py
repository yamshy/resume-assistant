from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from fastapi import Depends

from app.core.settings import SettingsDep
from resume_core.services.profile_service import ProfileService
from resume_core.services.resume_service import ResumeService
from resume_core.services.storage_service import StorageService


@lru_cache
def _storage_from_base_path(base_path: str) -> StorageService:
    return StorageService(Path(base_path))


def get_storage_service(settings: SettingsDep) -> StorageService:
    return _storage_from_base_path(str(settings.STORAGE_BASE_DIR))


def get_profile_service(
    settings: SettingsDep,
    storage: StorageService = Depends(get_storage_service),
) -> ProfileService:
    return ProfileService(storage, profile_path=settings.resolved_profile_path)


def get_resume_service(
    settings: SettingsDep,
    profile_service: ProfileService = Depends(get_profile_service),
    storage: StorageService = Depends(get_storage_service),
) -> ResumeService:
    return ResumeService(
        profile_service=profile_service,
        storage_service=storage,
        resumes_dir=settings.resolved_resumes_dir,
    )
