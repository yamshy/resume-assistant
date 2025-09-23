from typing import Any, cast

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
from app.ingestion import ParsedResume, ResumeIngestor


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

    resolver_calls: list[None] = []

    def fake_resolver():
        resolver_calls.append(None)
        return None

    monkeypatch.setattr(
        "app.agents.ingestion_agent.resolve_ingestion_client",
        fake_resolver,
    )

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
    assert resolver_calls, "Expected ingestion client resolver to be consulted"

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


@pytest.mark.asyncio
async def test_call_llm_uses_structured_client():
    agent = ResumeIngestionAgent()

    class DummyCompletions:
        def __init__(self) -> None:
            self.calls: list[dict[str, Any]] = []

        async def create(self, **kwargs: Any):
            self.calls.append(kwargs)
            response_model = kwargs["response_model"]
            return response_model()

    class DummyChat:
        def __init__(self, completions: DummyCompletions) -> None:
            self.completions = completions

    class DummyClient:
        def __init__(self, completions: DummyCompletions) -> None:
            self.chat = DummyChat(completions)

    completions = DummyCompletions()
    dummy_client = DummyClient(completions)
    agent._client = cast(Any, dummy_client)

    result = await agent._call_llm("plan", {"focus": "contacts"}, PlanModel)

    assert isinstance(result, PlanModel)
    assert completions.calls, "Expected the structured client to be invoked"
    call = completions.calls[0]
    assert call["model"] == agent.model
    assert call["temperature"] == agent.temperature
    assert call["max_retries"] == agent.max_retries
    assert call["messages"][0]["role"] == "system"
    assert call["messages"][1]["role"] == "user"


def test_resume_ingestor_uses_resolved_client(monkeypatch):
    captured: dict[str, Any] = {}
    resolved_client = object()
    call_count = 0

    def fake_resolver():
        nonlocal call_count
        call_count += 1
        return resolved_client

    class DummyAgent:
        def __init__(self, *, tool_registry, client=None, **_: Any) -> None:
            captured["tool_registry"] = tool_registry
            captured["client"] = client

        async def ingest(self, source: str, text: str, notes: str | None = None):
            raise NotImplementedError

    monkeypatch.setattr("app.ingestion.resolve_ingestion_client", fake_resolver)
    monkeypatch.setattr("app.agents.ResumeIngestionAgent", DummyAgent)

    ingestor = ResumeIngestor(tools={})

    assert isinstance(ingestor.agent, DummyAgent)
    assert captured["client"] is resolved_client
    assert captured["tool_registry"] == {}
    assert call_count == 1
