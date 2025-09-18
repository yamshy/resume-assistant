from __future__ import annotations

from fastapi import APIRouter

from .resumes import _resume_service

router = APIRouter(tags=["history"])


@router.get("/resumes/history")
def list_history() -> dict[str, list]:
    return {"items": _resume_service.list_history()}
