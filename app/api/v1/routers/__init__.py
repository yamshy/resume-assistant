from fastapi import APIRouter

from . import health, jobs, profile, resumes

router = APIRouter()

router.include_router(health.router)
router.include_router(profile.router)
router.include_router(jobs.router)
router.include_router(resumes.router)

__all__ = ["router"]

