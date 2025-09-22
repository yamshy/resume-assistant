from datetime import date
from typing import Any, Dict, List

import pytest

from app.agents import ResumeGenerationAgent, ResumeGenerationTools
from app.models import Experience, Resume


class RecordingLLM:
    def __init__(self, responses: List[Resume]) -> None:
        self._responses = responses
        self.calls: List[Dict[str, Any]] = []

    async def generate(self, model: str, job_posting: str, context: Dict[str, Any]) -> Resume:
        index = len(self.calls)
        self.calls.append({"model": model, "job_posting": job_posting, "context": context})
        response = self._responses[index]
        return response.model_copy(deep=True)


class SequenceValidator:
    def __init__(self, scores: List[float]) -> None:
        self.scores = scores
        self.calls = 0

    async def validate(self, resume: Resume, context: Dict[str, Any]) -> Resume:
        index = min(self.calls, len(self.scores) - 1)
        resume.confidence_scores["overall"] = self.scores[index]
        self.calls += 1
        return resume


def build_resume(achievements: List[str], citations: Dict[str, str] | None = None) -> Resume:
    experience = Experience(
        company="Acme",
        role="Engineer",
        start_date=date(2020, 1, 1),
        achievements=achievements,
        location="Remote",
    )
    summary = (
        "Experienced engineer delivering measurable impact on distributed systems while "
        "aligning achievements with business goals."
    )
    return Resume(
        full_name="Taylor Candidate",
        email="taylor@example.com",
        phone="+1 555-0100",
        location="Remote",
        summary=summary,
        experiences=[experience],
        education=[],
        skills=["Python", "AWS"],
        citations=citations or {},
        confidence_scores={},
        metadata={},
    )


@pytest.mark.asyncio
async def test_agent_generates_resume_successfully():
    resume = build_resume(["Increased reliability by 40% through automation"])
    resume.citations = {"Increased reliability by 40% through automation": "doc"}
    llm = RecordingLLM([resume])
    validator = SequenceValidator([0.92])

    stored: List[Resume] = []
    metrics: List[Dict[str, Any]] = []

    async def cache_lookup(job: str, profile: Dict[str, Any]) -> Resume | None:
        return None

    async def cache_store(job: str, profile: Dict[str, Any], generated: Resume) -> None:
        stored.append(generated)

    async def build_context(job: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        return {"job_posting": job, "profile": profile}

    def select_model(job: str, profile: Dict[str, Any]) -> str:
        return "gpt-4o-mini"

    def estimate_tokens(resume: Resume) -> int:
        return 128

    async def monitor(model: str, tokens: int, latency: float, confidence: float, cache_hit: bool) -> None:
        metrics.append(
            {
                "model": model,
                "tokens": tokens,
                "latency": latency,
                "confidence": confidence,
                "cache_hit": cache_hit,
            }
        )

    tools = ResumeGenerationTools(
        cache_lookup=cache_lookup,
        cache_store=cache_store,
        build_context=build_context,
        select_model=select_model,
        estimate_tokens=estimate_tokens,
        monitor=monitor,
    )

    agent = ResumeGenerationAgent(
        llm=llm,
        validator=validator,
        max_retries=2,
        confidence_threshold=0.8,
    )

    result = await agent.generate("Senior Engineer", {"name": "Taylor"}, tools)

    assert result.metadata["validation_passed"] is True
    assert result.metadata["attempts"] == 1
    assert result.metadata["cached"] is False
    assert stored and stored[0] == result
    assert metrics and metrics[0]["cache_hit"] is False
    assert len(llm.calls) == 1
    assert "plan" in result.metadata


@pytest.mark.asyncio
async def test_agent_retries_with_validator_feedback():
    resumes = [
        build_resume(["Improved throughput by 20% via profiling"], {"Improved throughput by 20% via profiling": "doc"}),
        build_resume(["Improved throughput by 20% via profiling"], {"Improved throughput by 20% via profiling": "doc"}),
    ]
    llm = RecordingLLM(resumes)
    validator = SequenceValidator([0.6, 0.91])

    stored: List[Resume] = []

    async def cache_lookup(job: str, profile: Dict[str, Any]) -> Resume | None:
        return None

    async def cache_store(job: str, profile: Dict[str, Any], generated: Resume) -> None:
        stored.append(generated)

    async def build_context(job: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        return {"job_posting": job, "profile": profile}

    def select_model(job: str, profile: Dict[str, Any]) -> str:
        return "gpt-4o-mini"

    def estimate_tokens(resume: Resume) -> int:
        return 256

    metrics: List[Dict[str, Any]] = []

    async def monitor(model: str, tokens: int, latency: float, confidence: float, cache_hit: bool) -> None:
        metrics.append(
            {
                "model": model,
                "tokens": tokens,
                "latency": latency,
                "confidence": confidence,
                "cache_hit": cache_hit,
            }
        )

    tools = ResumeGenerationTools(
        cache_lookup=cache_lookup,
        cache_store=cache_store,
        build_context=build_context,
        select_model=select_model,
        estimate_tokens=estimate_tokens,
        monitor=monitor,
    )

    agent = ResumeGenerationAgent(
        llm=llm,
        validator=validator,
        max_retries=3,
        confidence_threshold=0.8,
    )

    result = await agent.generate("Staff Engineer", {"name": "Taylor"}, tools)

    assert len(llm.calls) == 2
    second_context = llm.calls[1]["context"]
    assert "validator_feedback" in second_context
    assert "Overall confidence" in second_context["validator_feedback"]
    assert result.metadata["attempts"] == 2
    assert result.metadata["validation_passed"] is True
    assert stored and stored[0] == result
    assert metrics[0]["cache_hit"] is False


@pytest.mark.asyncio
async def test_agent_returns_cached_resume_without_invoking_llm():
    cached_resume = build_resume(["Cut incident response time by 30% using playbooks"])
    cached_resume.citations = {"Cut incident response time by 30% using playbooks": "doc"}
    cached_resume.confidence_scores["overall"] = 0.95
    cached_resume.metadata = {"model": "gpt-4o-mini", "cached": True}
    llm = RecordingLLM([cached_resume])

    async def cache_lookup(job: str, profile: Dict[str, Any]) -> Resume | None:
        return cached_resume.model_copy(deep=True)

    async def cache_store(job: str, profile: Dict[str, Any], generated: Resume) -> None:
        raise AssertionError("cache_store should not be called on cache hit")

    async def build_context(job: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        return {"job_posting": job, "profile": profile}

    def select_model(job: str, profile: Dict[str, Any]) -> str:
        return "gpt-4o-mini"

    def estimate_tokens(resume: Resume) -> int:
        return 64

    metrics: List[Dict[str, Any]] = []

    async def monitor(model: str, tokens: int, latency: float, confidence: float, cache_hit: bool) -> None:
        metrics.append(
            {
                "model": model,
                "tokens": tokens,
                "latency": latency,
                "confidence": confidence,
                "cache_hit": cache_hit,
            }
        )

    tools = ResumeGenerationTools(
        cache_lookup=cache_lookup,
        cache_store=cache_store,
        build_context=build_context,
        select_model=select_model,
        estimate_tokens=estimate_tokens,
        monitor=monitor,
    )

    agent = ResumeGenerationAgent(
        llm=llm,
        max_retries=1,
        confidence_threshold=0.8,
    )

    result = await agent.generate("Engineering Manager", {"name": "Taylor"}, tools)

    assert result.metadata["cached"] is True
    assert result.metadata["tokens"] == 64
    assert metrics and metrics[0]["cache_hit"] is True
    assert len(llm.calls) == 0
