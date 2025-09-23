import pytest

from app.agents.ingestion_agent import (
    ExtractionExperienceModel,
    ExtractionModel,
    MissingIngestionLLMError,
    PlanModel,
    PlanStepModel,
    ResumeIngestionAgent,
    ResumeIngestionError,
    VerificationFeedback,
)
from app.ingestion import ParsedResume


@pytest.mark.asyncio
async def test_ingestion_agent_runs_plan_flow(monkeypatch):
    resume_text = """
    Alex Example
    alex@example.com | +1 555-0200
    Skills: Kubernetes, Terraform, Observability
    Principal SRE at CloudWorks
    - Drove SOC2 automation and reduced security review cycles by 50%
    - Built global observability platform adopted by 45 teams
    """.strip()

    class DummyLLM:
        def __init__(self) -> None:
            self.client = object()

    llm_calls: list[str] = []
    agent = ResumeIngestionAgent(llm=DummyLLM())

    async def fake_call_llm(self, stage, payload, response_model):  # type: ignore[override]
        llm_calls.append(stage)
        if stage == "plan":
            return PlanModel(
                goal="Extract resume fields",
                steps=[
                    PlanStepModel(
                        name="collect_contacts",
                        description="Gather contact details",
                        tool=None,
                    )
                ],
            )
        if stage == "extract":
            return ExtractionModel(
                full_name="Alex Example",
                email="alex@example.com",
                phone="+1 555-0200",
                skills=["Python", "Kubernetes"],
                experiences=[
                    ExtractionExperienceModel(
                        company="CloudWorks",
                        role="Principal SRE",
                        achievements=[
                            "Reduced security review cycles by 50%",
                            "Built global observability platform",
                        ],
                        start_date="2020-01-01",
                        end_date="2024-01-01",
                        location="Remote",
                    )
                ],
            )
        if stage == "verify":
            return VerificationFeedback(corrections={"phone": "+1 555-0300"})
        raise ResumeIngestionError(f"Unexpected stage {stage}")

    monkeypatch.setattr(ResumeIngestionAgent, "_call_llm", fake_call_llm, raising=False)

    parsed = await agent.ingest("resume.txt", resume_text)

    assert isinstance(parsed, ParsedResume)
    assert parsed.full_name == "Alex Example"
    assert parsed.phone == "+1 555-0300"
    assert parsed.skills == ["Python", "Kubernetes"]
    assert parsed.experiences
    assert parsed.experiences[0].achievements == [
        "Reduced security review cycles by 50%",
        "Built global observability platform",
    ]
    assert llm_calls == ["plan", "extract", "verify"]


def test_ingestion_agent_requires_llm(monkeypatch):
    class DummyLLM:
        client = None

    monkeypatch.setattr("app.agents.ingestion_agent.resolve_llm", lambda: DummyLLM())

    with pytest.raises(MissingIngestionLLMError):
        ResumeIngestionAgent()


@pytest.mark.asyncio
async def test_call_llm_raises_when_chat_fails():
    class FakeCompletions:
        async def create(self, **kwargs):  # type: ignore[no-untyped-def]
            raise RuntimeError("boom")

    class FakeChat:
        def __init__(self) -> None:
            self.completions = FakeCompletions()

    class FakeClient:
        def __init__(self) -> None:
            self.chat = FakeChat()

    class FakeLLM:
        def __init__(self) -> None:
            self.client = FakeClient()

    agent = ResumeIngestionAgent(llm=FakeLLM())

    with pytest.raises(MissingIngestionLLMError):
        await agent._call_llm("plan", {}, PlanModel)
