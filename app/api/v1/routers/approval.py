from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Path, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.dependencies import get_resume_service
from resume_core.models.approval import ApprovalOutcome
from resume_core.services.resume_service import ResumeService

router = APIRouter(tags=["approval"])


class ApprovalRequest(BaseModel):
    decision: str = Field(description="User decision for the tailored resume")
    feedback: str | None = Field(default=None, description="Optional review feedback")
    reviewer: str | None = Field(default=None, description="Reviewer identifier")
    approved_sections: list[str] = Field(default_factory=list)
    rejected_sections: list[str] = Field(default_factory=list)


@router.post(
    "/resumes/{resume_id}/approve",
    response_model=ApprovalOutcome,
    status_code=status.HTTP_200_OK,
)
async def approve_resume(
    approval: ApprovalRequest,
    resume_id: UUID = Path(..., description="Identifier of the tailored resume"),
    resume_service: ResumeService = Depends(get_resume_service),
) -> ApprovalOutcome:
    try:
        return await resume_service.approve_resume(
            resume_id=str(resume_id),
            decision=approval.decision,
            feedback=approval.feedback,
            reviewer=approval.reviewer,
            approved_sections=approval.approved_sections,
            rejected_sections=approval.rejected_sections,
        )
    except FileNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "resume_not_found"},
        )
