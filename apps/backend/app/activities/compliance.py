from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field
from temporalio import activity

from ..state import AgentConfig
from . import get_registry


class ComplianceInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    resume_markdown: str
    profile: Dict[str, Any] = Field(default_factory=dict)
    config: AgentConfig


class ComplianceResult(BaseModel):
    report: Dict[str, Any]
    audit_event: str
    status: str


@activity.defn
async def run_compliance_check(payload: ComplianceInput) -> ComplianceResult:
    """Run compliance review using the configured LLM."""

    if not payload.resume_markdown:
        raise ValueError("draft_resume missing before compliance checks")
    registry = get_registry()
    policy = {
        "blocklist": list(payload.config.compliance_blocklist),
        "profile": payload.profile,
    }
    review = registry.llm.compliance_review(payload.resume_markdown, policy)
    status = review.get("status", "approved")
    violations = review.get("violations", [])
    report = {"status": status, "violations": violations}
    audit_label = "compliance.rejected" if status == "rejected" else "compliance.approved"
    return ComplianceResult(report=report, audit_event=audit_label, status=status)


__all__ = ["ComplianceInput", "ComplianceResult", "run_compliance_check"]
