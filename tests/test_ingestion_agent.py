import pytest

from app.agents.ingestion_agent import (
    ExtractionModel,
    MissingIngestionLLMError,
    PlanModel,
    PlanStepModel,
    ResumeIngestionAgent,
    VerificationFeedback,
)
from app.ingestion import ParsedExperience, ParsedResume, ResumeIngestor


class StubCompletions:
    def __init__(self, responses: dict[str, object]) -> None:
        self._responses = responses
        self.calls: list[str] = []

    async def create(self, model, response_model, messages, temperature, max_retries):  # noqa: D401
        system_message = messages[0]["content"]
        stage = system_message.split("stage: ")[1].split(".")[0]
        self.calls.append(stage)
        return self._responses[stage]


class StubChat:
    def __init__(self, completions: StubCompletions) -> None:
        self.completions = completions


class StubClient:
    def __init__(self, responses: dict[str, object]) -> None:
        self._completions = StubCompletions(responses)
        self.chat = StubChat(self._completions)

    @property
    def calls(self) -> list[str]:
        return self._completions.calls


class StubLLM:
    def __init__(self, responses: dict[str, object]) -> None:
        self.client = StubClient(responses)

    @property
    def calls(self) -> list[str]:
        return self.client.calls


@pytest.mark.asyncio
async def test_ingestion_agent_uses_llm_responses():
    resume_text = """
    Alex Example
    alex@example.com | +1 555-0200
    Principal SRE at CloudWorks
    - Reduced latency by 30% through observability improvements
    """.strip()

    responses = {
        "plan": PlanModel(
            goal="Extract resume fields",
            steps=[
                PlanStepModel(
                    name="collect_contacts",
                    description="Ensure contact information is captured",
                )
            ],
        ),
        "extract": ExtractionModel(
            full_name="Alex Example",
            email="alex@example.com",
            phone="+1 555-0200",
            skills=["Python", "python", "Go"],
            experiences=[
                {
                    "company": "CloudWorks",
                    "role": "Principal SRE",
                    "achievements": ["  Reduced latency by 30% through observability improvements  "],
                }
            ],
        ),
        "verify": VerificationFeedback(corrections={"phone": "+1 555-0300"}),
    }

    stub_llm = StubLLM(responses)
    agent = ResumeIngestionAgent(llm=stub_llm, model="stub-model", temperature=0, max_retries=0)

    parsed = await agent.ingest("resume.txt", resume_text, notes="Highlights reliability work")

    assert isinstance(parsed, ParsedResume)
    assert parsed.full_name == "Alex Example"
    assert parsed.email == "alex@example.com"
    assert parsed.phone == "+1 555-0300"
    assert parsed.skills == ["Python", "Go"]
    assert parsed.experiences[0].company == "CloudWorks"
    assert parsed.experiences[0].achievements == [
        "Reduced latency by 30% through observability improvements"
    ]
    assert stub_llm.calls == ["plan", "extract", "verify"]


@pytest.mark.asyncio
async def test_ingestor_normalises_agent_payload():
    class StubAgent:
        async def ingest(self, source: str, text: str, notes: str | None = None) -> object:
            return {
                "full_name": "Taylor Example",
                "email": "taylor@example.com",
                "phone": "+1 555-0400",
                "skills": ["Python", "python", "Go"],
                "experiences": [
                    ParsedExperience(
                        company="Fallback Labs",
                        role="Engineer",
                        achievements=[" Reduced incidents by 40% ", ""],
                        start_date="2021",
                    ),
                    {
                        "company": "Legacy Corp",
                        "role": "Lead",
                        "achievements": ["Scaled platform availability"],
                        "location": "Remote",
                    },
                ],
            }

    ingestor = ResumeIngestor(agent=StubAgent())
    parsed = await ingestor.parse("resume.txt", "Taylor Example")

    assert parsed.full_name == "Taylor Example"
    assert parsed.skills == ["Python", "Go"]
    assert [exp.company for exp in parsed.experiences] == [
        "Fallback Labs",
        "Legacy Corp",
    ]
    assert parsed.experiences[0].achievements == ["Reduced incidents by 40%"]
    assert parsed.experiences[1].location == "Remote"


def test_ingestion_agent_requires_llm_client():
    class NoClientLLM:
        pass

    with pytest.raises(MissingIngestionLLMError):
        ResumeIngestionAgent(llm=NoClientLLM())
