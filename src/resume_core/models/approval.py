from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class ReviewDecision(BaseModel):
    decision: str
    comments: str | None = None
    reviewer: str = "user"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ApprovalWorkflow(BaseModel):
    resume_id: str
    status: str
    history: list[ReviewDecision] = Field(default_factory=list)

    def record(self, decision: ReviewDecision) -> None:
        self.history.append(decision)
        self.status = (
            decision.decision if decision.decision != "changes_requested" else "changes_requested"
        )
