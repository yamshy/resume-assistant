from types import SimpleNamespace

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
from app.ingestion import ParsedExperience, ParsedResume, ResumeIngestor


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


@pytest.mark.asyncio
async def test_call_llm_uses_explicit_client(monkeypatch):
    agent = ResumeIngestionAgent(tool_registry=default_tool_registry())

    class FakeCompletions:
        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        async def create(self, **kwargs):
            self.calls.append(kwargs)
            return PlanModel(goal="ingest")

    completions = FakeCompletions()
    agent._client = SimpleNamespace(chat=SimpleNamespace(completions=completions))

    result = await agent._call_llm("plan", {"payload": True}, PlanModel)

    assert isinstance(result, PlanModel)
    assert result.goal == "ingest"
    assert completions.calls, "Expected structured client to receive a call"


@pytest.mark.asyncio
async def test_ingestor_and_agent_normalise_identically(monkeypatch):
    resume_text = """
    Taylor Example
    taylor@example.com | +1 555-222-0100
    Skills: Python, Rust, Go
    Experience Highlights
    - Championed observability improvements across the platform
    """.strip()

    agent = ResumeIngestionAgent(tool_registry=default_tool_registry())

    async def fake_call_llm(self, stage, payload, response_model):  # type: ignore[override]
        if stage == "plan":
            return PlanModel(
                goal="Ensure resume fields are extracted",
                steps=[
                    PlanStepModel(
                        name="collect",
                        description="Collect skills and experience blocks",
                        tool="extract_skills",
                    )
                ],
            )
        if stage == "extract":
            return ExtractionModel(
                full_name=None,
                email=None,
                phone=None,
                skills=["Python", "python", "Rust"],
                experiences=[],
            )
        if stage == "verify":
            return VerificationFeedback()
        return None

    monkeypatch.setattr(ResumeIngestionAgent, "_call_llm", fake_call_llm, raising=False)

    original_maybe_invoke = ResumeIngestionAgent._maybe_invoke

    async def fake_maybe_invoke(self, tool_name, text):
        if tool_name == "extract_skills":
            return ["python", "Go", " rust "]
        if tool_name == "extract_experiences":
            return [
                {
                    "company": "Fallback Labs",
                    "role": "",
                    "achievements": ["  Shipped ML platform  ", ""],
                    "start_date": "2020",
                    "location": "Remote",
                },
                ParsedExperience(
                    company="Legacy Corp",
                    role="Engineer",
                    achievements=["Maintained critical systems", ""],
                    end_date="2019",
                ),
            ]
        return await original_maybe_invoke(self, tool_name, text)

    monkeypatch.setattr(ResumeIngestionAgent, "_maybe_invoke", fake_maybe_invoke, raising=False)

    parsed_agent = await agent.ingest("resume.txt", resume_text)

    ingestor = ResumeIngestor(agent=agent)
    parsed_ingestor = await ingestor.parse("resume.txt", resume_text)

    assert parsed_agent == parsed_ingestor
    assert parsed_agent.skills == ["Python", "Rust", "Go"]
    assert [exp.company for exp in parsed_agent.experiences] == [
        "Fallback Labs",
        "Legacy Corp",
    ]
    assert parsed_agent.experiences[0].role == "Professional"
    assert parsed_agent.experiences[0].achievements == ["Shipped ML platform"]
    assert parsed_agent.experiences[0].location == "Remote"
    assert parsed_agent.experiences[1].achievements == ["Maintained critical systems"]
    assert parsed_agent.experiences[1].end_date == "2019"


def test_ingestor_resolves_ingestion_client(monkeypatch):
    captured: dict[str, object] = {}

    class FakeAgent:
        def __init__(self, *, tool_registry, client):
            captured["client"] = client
            self.tool_registry = tool_registry

    monkeypatch.setattr("app.ingestion.resolve_ingestion_client", lambda: "sentinel-client")
    monkeypatch.setattr("app.agents.ResumeIngestionAgent", FakeAgent)
    monkeypatch.setattr("app.agents.ingestion_agent.ResumeIngestionAgent", FakeAgent)

    ingestor = ResumeIngestor(tools={})

    assert isinstance(ingestor.agent, FakeAgent)
    assert captured["client"] == "sentinel-client"
