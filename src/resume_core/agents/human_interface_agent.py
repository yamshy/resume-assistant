from __future__ import annotations

import json
from typing import Sequence

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.function import FunctionModel

from resume_core.models.approval import ApprovalDecision, ApprovalDecisionType
from resume_core.models.resume import TailoredResume


class HumanInterfaceAgent:
    def __init__(self) -> None:
        self._agent = Agent(FunctionModel(self._run), name="human-interface-agent")

    async def review(
        self,
        resume: TailoredResume,
        decision: str,
        feedback: str | None = None,
        reviewer: str | None = None,
        approved_sections: list[str] | None = None,
        rejected_sections: list[str] | None = None,
    ) -> ApprovalDecision:
        payload = {
            "resume": resume.model_dump(mode="json"),
            "decision": decision,
            "feedback": feedback,
            "reviewer": reviewer,
            "approved_sections": approved_sections or [],
            "rejected_sections": rejected_sections or [],
        }
        result = await self._agent.run(json.dumps(payload))
        return ApprovalDecision.model_validate(json.loads(result.output))

    async def _run(
        self,
        messages: Sequence[ModelMessage],
        agent_info,  # noqa: ANN001
    ) -> ModelResponse:
        text = _extract_user_text(messages)
        payload = json.loads(text)
        resume = TailoredResume.model_validate(payload["resume"])
        decision = payload.get("decision", "pending")
        feedback = payload.get("feedback")
        reviewer = payload.get("reviewer")
        approved_sections = payload.get("approved_sections", [])
        rejected_sections = payload.get("rejected_sections", [])
        approval = self._apply_decision(
            resume,
            decision,
            feedback,
            reviewer,
            approved_sections,
            rejected_sections,
        )
        return ModelResponse(parts=[TextPart(approval.model_dump_json())], model_name="function:human-interface")

    def _apply_decision(
        self,
        resume: TailoredResume,
        decision: str,
        feedback: str | None,
        reviewer: str | None,
        approved_sections: list[str],
        rejected_sections: list[str],
    ) -> ApprovalDecision:
        normalized = _normalize_decision(decision)
        return ApprovalDecision(
            decision=normalized,
            feedback=feedback,
            reviewer=reviewer,
            approved_sections=approved_sections,
            rejected_sections=rejected_sections,
        )


def _normalize_decision(decision: str) -> ApprovalDecisionType:
    try:
        return ApprovalDecisionType(decision.lower())
    except ValueError:
        return ApprovalDecisionType.PENDING


def _extract_user_text(messages: Sequence[ModelMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, UserPromptPart):
                    return str(part.content)
    return ""
