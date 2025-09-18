from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from resume_core.models.approval import ApprovalWorkflow
from resume_core.utils.errors import NotFoundError

from .resumes import _resume_service

router = APIRouter(tags=["approval"])


class ApprovalRequest(BaseModel):
    decision: str
    comments: str | None = None


@router.post("/resumes/{resume_id}/approve")
async def approve_resume(resume_id: UUID, request: ApprovalRequest) -> dict[str, object]:
    try:
        workflow: ApprovalWorkflow = await _resume_service.approve_resume(
            resume_id=str(resume_id),
            decision=request.decision,
            comments=request.comments,
        )
    except FileNotFoundError as exc:  # pragma: no cover - mapped to HTTP
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:  # invalid decision
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except NotFoundError as exc:  # pragma: no cover
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    latest_decision = workflow.history[-1].model_dump()
    return {
        "resume_id": workflow.resume_id,
        "status": workflow.status,
        "decision": latest_decision,
        "history": [decision.model_dump() for decision in workflow.history],
    }
