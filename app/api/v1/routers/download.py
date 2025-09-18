from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException

from .resumes import _resume_service

router = APIRouter(tags=["download"])


@router.get("/resumes/{resume_id}/download")
def download_resume(resume_id: UUID) -> dict[str, str]:
    try:
        return _resume_service.download_resume(str(resume_id))
    except FileNotFoundError as exc:  # pragma: no cover - error mapping
        raise HTTPException(status_code=404, detail=str(exc)) from exc
