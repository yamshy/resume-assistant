from __future__ import annotations

from fastapi import APIRouter

from resume_core.models.profile import UserProfile
from resume_core.services.profile_service import ProfileService

router = APIRouter(tags=["profile"])
_profile_service = ProfileService()


@router.get("/profile")
def get_profile() -> dict[str, dict]:
    profile = _profile_service.load_profile()
    return {"profile": profile.model_dump()}


@router.put("/profile")
def update_profile(payload: UserProfile) -> dict[str, dict]:
    saved = _profile_service.save_profile(payload)
    return {"profile": saved.model_dump()}
