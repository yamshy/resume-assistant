import pytest

from app.agents.ingestion_agent import (
    AgentTool,
    ExtractionModel,
    PlanModel,
    PlanStepModel,
    ResumeIngestionAgent,
    VerificationFeedback,
    default_tool_registry,
)
from app.ingestion import ParsedResume


@pytest.mark.asyncio
async def test_ingestion_agent_runs_plan_and_tools(monkeypatch):
    resume_text = """
    Alex Example
    alex@example.com | +1 555-0200
    Skills: Kubernetes, Terraform, Observability
    Principal SRE at CloudWorks
    - Drove SOC2 automation and reduced security review cycles by 50%
    - Built global observability platform adopted by 45 teams
    """.strip()

    llm_calls: list[str] = []
    tools = default_tool_registry()
    original_email_tool = tools["extract_email"]
    email_invocations: list[str] = []

    def recording_email_tool(text: str) -> str | None:
        email_invocations.append(text)
        return original_email_tool.func(text)

    tools["extract_email"] = AgentTool(
        name=original_email_tool.name,
        description=original_email_tool.description,
        func=recording_email_tool,
    )

    agent = ResumeIngestionAgent(tool_registry=tools)

    async def fake_call_llm(self, stage, payload, response_model):  # type: ignore[override]
        llm_calls.append(stage)
        if stage == "plan":
            return PlanModel(
                goal="Extract resume fields",
                steps=[
                    PlanStepModel(
                        name="contacts",
                        description="Call extract_email tool",
                        tool="extract_email",
                    )
                ],
            )
        if stage == "extract":
            return ExtractionModel(full_name="Alex Example", skills=["Python"], experiences=[])
        if stage == "verify":
            return VerificationFeedback(missing_fields=["email"])
        return None

    monkeypatch.setattr(ResumeIngestionAgent, "_call_llm", fake_call_llm, raising=False)

    parsed = await agent.ingest("resume.txt", resume_text)

    assert isinstance(parsed, ParsedResume)
    assert parsed.full_name == "Alex Example"
    assert parsed.email == "alex@example.com"
    assert parsed.skills
    assert parsed.experiences
    assert llm_calls == ["plan", "extract", "verify"]
    assert email_invocations, "Expected email tool to be invoked"
