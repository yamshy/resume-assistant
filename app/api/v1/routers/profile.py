from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_tailoring_service
from resume_core.models import UserProfile
from resume_core.services import ResumeTailoringService

router = APIRouter(tags=["profile"])


@router.get("/profile", response_model=UserProfile)
async def get_profile(service: ResumeTailoringService = Depends(get_tailoring_service)) -> UserProfile:
    profile = service.profile_store.get_profile()
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile


@router.put("/profile", response_model=UserProfile)
async def update_profile(
    profile: UserProfile,
    service: ResumeTailoringService = Depends(get_tailoring_service),
) -> UserProfile:
    return service.profile_store.save_profile(profile)

