from types import SimpleNamespace

import httpx
import pytest
from openai import AuthenticationError

from app.agents.ingestion_agent import (
    ExtractionExperienceModel,
    ExtractionModel,
    IngestionAgentError,
    MissingIngestionLLMError,
    PlanModel,
    PlanStepModel,
    ResumeIngestionAgent,
    VerificationFeedback,
)
from app.ingestion import ParsedResume, ResumeIngestor


class FakeCompletions:
    def __init__(self, responses: list[object]) -> None:
        self.calls: list[dict[str, object]] = []
        self._responses = responses

    async def create(self, **kwargs):  # type: ignore[no-untyped-def]
        self.calls.append(kwargs)
        if not self._responses:
            raise AssertionError("Unexpected LLM invocation")
        return self._responses.pop(0)


class FakeInstructor:
    def __init__(self, responses: list[object]) -> None:
        self.chat = SimpleNamespace(completions=FakeCompletions(responses))


@pytest.mark.asyncio
async def test_ingestion_agent_processes_structured_llm_responses() -> None:
    resume_text = """
    Alex Example
    alex@example.com | +1 555-0200
    Skills: Python, Rust, Terraform
    Principal SRE at CloudWorks
    - Drove SOC2 automation and reduced security review cycles by 50%
    - Built global observability platform adopted by 45 teams
    """.strip()

    responses: list[object] = [
        PlanModel(
            goal="Extract resume fields",
            steps=[
                PlanStepModel(
                    name="collect_contacts",
                    description="Ensure contact details are captured",
                )
            ],
        ),
        ExtractionModel(
            full_name="Alex Example",
            email=None,
            phone=None,
            skills=["Python", "Rust", "python"],
            experiences=[
                ExtractionExperienceModel(
                    company="CloudWorks",
                    role="Principal SRE",
                    achievements=[
                        "Drove SOC2 automation and reduced review cycles by 50%",
                        "Built global observability platform",
                    ],
                )
            ],
        ),
        VerificationFeedback(
            corrections={"email": "alex@example.com"},
            missing_fields=[],
        ),
    ]

    agent = ResumeIngestionAgent(client=FakeInstructor(responses))

    parsed = await agent.ingest("resume.txt", resume_text)

    assert isinstance(parsed, ParsedResume)
    assert parsed.source == "resume.txt"
    assert parsed.full_name == "Alex Example"
    assert parsed.email == "alex@example.com"
    assert parsed.phone is None
    assert parsed.skills == ["Python", "Rust"]
    assert parsed.experiences
    assert parsed.experiences[0].company == "CloudWorks"
    assert parsed.experiences[0].achievements


@pytest.mark.asyncio
async def test_call_llm_raises_ingestion_error_when_completion_fails() -> None:
    class FailingCompletions:
        async def create(self, **kwargs):  # type: ignore[no-untyped-def]
            raise RuntimeError("boom")

    client = SimpleNamespace(chat=SimpleNamespace(completions=FailingCompletions()))
    agent = ResumeIngestionAgent(client=client)

    with pytest.raises(IngestionAgentError):
        await agent._call_llm("plan", {"payload": True}, PlanModel)


@pytest.mark.asyncio
async def test_call_llm_maps_authentication_errors_to_missing_llm() -> None:
    class AuthFailingCompletions:
        async def create(self, **kwargs):  # type: ignore[no-untyped-def]
            request = httpx.Request("POST", "https://api.openai.com/v1/test")
            raise AuthenticationError(
                "Invalid API key",
                response=httpx.Response(401, request=request),
                body=None,
            )

    client = SimpleNamespace(chat=SimpleNamespace(completions=AuthFailingCompletions()))
    agent = ResumeIngestionAgent(client=client)

    with pytest.raises(MissingIngestionLLMError):
        await agent._call_llm("plan", {"payload": True}, PlanModel)


def test_ingestion_agent_requires_configured_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(MissingIngestionLLMError):
        ResumeIngestionAgent()


def test_ingestor_resolves_ingestion_client(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class FakeAgent:
        def __init__(self, *, client):
            captured["client"] = client

        async def ingest(self, *args, **kwargs):  # type: ignore[no-untyped-def]
            raise AssertionError("Not expected during construction")

    monkeypatch.setattr("app.ingestion.resolve_ingestion_client", lambda: "sentinel-client")
    monkeypatch.setattr("app.agents.ResumeIngestionAgent", FakeAgent)
    monkeypatch.setattr("app.agents.ingestion_agent.ResumeIngestionAgent", FakeAgent)

    ingestor = ResumeIngestor()

    assert captured["client"] == "sentinel-client"
    assert isinstance(ingestor, ResumeIngestor)
