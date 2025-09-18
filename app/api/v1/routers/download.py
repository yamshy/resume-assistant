from __future__ import annotations

from enum import Enum
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Response, status
from fastapi.responses import JSONResponse

from app.api.dependencies import get_resume_service
from resume_core.services.resume_service import ResumeService

router = APIRouter(tags=["resumes"])


class DownloadFormat(str, Enum):
    MARKDOWN = "markdown"
    PDF = "pdf"
    DOCX = "docx"


@router.get("/resumes/{resume_id}/download")
async def download_resume(
    resume_id: UUID = Path(..., description="Identifier of the tailored resume"),
    format: str = Query(
        DownloadFormat.MARKDOWN.value,
        description="Requested download format",
    ),
    resume_service: ResumeService = Depends(get_resume_service),
) -> Response:
    requested_format = format.lower()
    if requested_format not in {item.value for item in DownloadFormat}:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "unsupported_format"},
        )

    try:
        download = await resume_service.download_resume(
            str(resume_id), requested_format
        )
    except FileNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "resume_not_found"},
        )

    headers = {
        "Content-Disposition": f'attachment; filename="{download.filename}"'
    }
    return Response(content=download.content, media_type=download.media_type, headers=headers)
