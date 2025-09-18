from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.api.dependencies import get_profile_service
from resume_core.models.profile import UserProfile
from resume_core.services.profile_service import ProfileService

router = APIRouter(tags=["profile"])


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@router.get("/profile", response_model=UserProfile)
async def get_profile(profile_service: ProfileService = Depends(get_profile_service)) -> UserProfile | JSONResponse:
    profile = await profile_service.load_profile()
    if profile is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "profile_not_found", "timestamp": _timestamp()},
        )
    return profile


@router.put("/profile", response_model=UserProfile)
async def put_profile(
    payload: UserProfile,
    profile_service: ProfileService = Depends(get_profile_service),
) -> UserProfile:
    saved = await profile_service.save_profile(payload)
    return saved
