from __future__ import annotations

from typing import Any

from resume_core.agents.base_agent import FunctionBackedAgent
from resume_core.models.approval import ReviewDecision
from resume_core.models.resume import TailoredResume
from resume_core.models.validation import ValidationResult


class HumanInterfaceAgent(FunctionBackedAgent[ReviewDecision]):
    def __init__(self) -> None:
        super().__init__(
            name="human-interface-agent",
            instructions="Recommend the next action for a human reviewer based on validation output.",
            output_model=ReviewDecision,
        )

    def build_output(self, payload: dict[str, Any]) -> ReviewDecision:
        validation = ValidationResult.model_validate(payload.get("validation") or {})
        resume = TailoredResume.model_validate(payload.get("resume") or {})
        if validation.passed and validation.score >= 0.7:
            return ReviewDecision(decision="approved", comments="Draft is ready for submission.")
        if resume.summary and validation.passed:
            return ReviewDecision(
                decision="changes_requested",
                comments="Consider refining highlighted skills before approval.",
            )
        return ReviewDecision(
            decision="changes_requested",
            comments="Resolve validation issues before seeking approval.",
        )

    async def review(
        self,
        *,
        resume: TailoredResume,
        validation: ValidationResult,
    ) -> ReviewDecision:
        payload = {
            "resume": resume.model_dump(),
            "validation": validation.model_dump(),
        }
        return await self.run(payload)
