"""
Approval workflow endpoints for Resume Assistant API.

Handles human-in-the-loop approval decisions for tailored resumes
with session management and export functionality.

Constitutional compliance:
- Thin FastAPI route handlers (no business logic)
- Delegates to storage and export services
- Structured error responses
- Standard REST patterns
"""

from enum import Enum
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from services.storage_service import create_storage_service


class ApprovalDecision(str, Enum):
    """Approval decision options."""

    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"


class ApprovalRequest(BaseModel):
    """Request model for approval decisions."""

    decision: ApprovalDecision
    comments: str | None = None
    requested_changes: str | None = None


class ApprovalResponse(BaseModel):
    """Response model for approval operations."""

    session_id: str
    decision: ApprovalDecision
    export_path: str | None = None
    message: str
    timestamp: str


# Create router for approval endpoints
router = APIRouter(prefix="/resumes", tags=["approval"])

# Initialize storage service
storage_service = create_storage_service()


@router.post("/{session_id}/approve", response_model=ApprovalResponse)
async def approve_resume(session_id: str, request: ApprovalRequest) -> ApprovalResponse:
    """
    Submit approval decision for a tailored resume.

    Handles human approval workflow decisions including approve, reject,
    or request changes. Approved resumes are exported to files.

    Args:
        session_id: Session identifier from tailoring request
        request: Approval decision and optional comments

    Returns:
        ApprovalResponse: Confirmation of decision and export path if approved

    Raises:
        HTTPException: If session not found or approval fails
    """
    try:
        # Load session data
        session_data = await storage_service.load_session_data(session_id)
        if session_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found"
            )

        # Extract pipeline results
        pipeline_results = session_data.get("pipeline_results", {})
        tailored_resume = pipeline_results.get("tailored_resume")
        job_analysis = pipeline_results.get("job_analysis")

        if not tailored_resume or not job_analysis:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Session data is incomplete - missing resume or job analysis",
            )

        export_path = None
        message = ""

        # Handle approval decision
        if request.decision == ApprovalDecision.APPROVE:
            # Export approved resume
            export_path = await storage_service.export_resume(
                tailored_resume=tailored_resume,
                job_title=job_analysis.job_title,
                company_name=job_analysis.company_name,
                session_id=session_id,
            )
            message = f"Resume approved and exported to {export_path}"

        elif request.decision == ApprovalDecision.REJECT:
            message = "Resume rejected. Session data preserved for reference."
            if request.comments:
                message += f" Comments: {request.comments}"

        elif request.decision == ApprovalDecision.REQUEST_CHANGES:
            message = "Changes requested. Session data preserved for revision."
            if request.requested_changes:
                message += f" Requested changes: {request.requested_changes}"

        # Update session data with approval decision
        session_data["approval_decision"] = {
            "decision": request.decision.value,
            "comments": request.comments,
            "requested_changes": request.requested_changes,
            "decided_at": pipeline_results.get("timestamps", {}).get("completed_at"),
            "export_path": export_path,
        }

        # Save updated session data
        await storage_service.save_session_data(session_id, session_data)

        from datetime import datetime

        return ApprovalResponse(
            session_id=session_id,
            decision=request.decision,
            export_path=export_path,
            message=message,
            timestamp=datetime.now().isoformat(),
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Approval validation error: {str(e)}",
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Approval processing error: {str(e)}",
        ) from e


@router.get("/{session_id}/status")
async def get_approval_status(session_id: str) -> dict[str, Any]:
    """
    Get approval status for a tailored resume session.

    Args:
        session_id: Session identifier

    Returns:
        Dict with approval status and metadata

    Raises:
        HTTPException: If session not found
    """
    try:
        session_data = await storage_service.load_session_data(session_id)
        if session_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found"
            )

        # Check for existing approval decision
        approval_decision = session_data.get("approval_decision")

        # Get pipeline results for status
        pipeline_results = session_data.get("pipeline_results", {})
        approval_workflow = pipeline_results.get("approval_workflow", {})

        return {
            "session_id": session_id,
            "requires_human_review": approval_workflow.get("requires_human_review", True),
            "auto_approved": approval_workflow.get("decision") == "auto_approve",
            "human_decision": approval_decision.get("decision") if approval_decision else None,
            "comments": approval_decision.get("comments") if approval_decision else None,
            "export_path": approval_decision.get("export_path") if approval_decision else None,
            "decided_at": approval_decision.get("decided_at") if approval_decision else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get approval status: {str(e)}",
        ) from e


__all__ = ["router", "ApprovalRequest", "ApprovalResponse", "ApprovalDecision"]
