from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query, Response, status
from fastapi.responses import JSONResponse, PlainTextResponse

from app.api.dependencies import get_resume_service
from resume_core.services.resume_service import ResumeService

router = APIRouter(tags=["resumes"])


@router.get("/resumes/{resume_id}/download", response_class=PlainTextResponse)
async def download_resume(
    resume_id: str = Path(..., description="Identifier of the tailored resume"),
    format: str = Query("markdown", description="Requested download format"),
    resume_service: ResumeService = Depends(get_resume_service),
) -> Response:
    if format.lower() != "markdown":
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "unsupported_format"},
        )

    markdown = await resume_service.download_markdown(resume_id)
    if markdown is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "resume_not_found"},
        )
    return PlainTextResponse(content=markdown, media_type="text/markdown")
