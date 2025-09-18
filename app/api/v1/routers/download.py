from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .resumes import _resume_service

router = APIRouter(tags=["download"])


@router.get("/resumes/{resume_id}/download")
def download_resume(resume_id: str) -> dict[str, str]:
    try:
        return _resume_service.download_resume(resume_id)
    except FileNotFoundError as exc:  # pragma: no cover - error mapping
        raise HTTPException(status_code=404, detail=str(exc)) from exc
