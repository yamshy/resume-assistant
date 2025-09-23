"""LLM client abstractions for resume generation."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Iterable, Protocol

import instructor
from openai import AsyncOpenAI

from .models import Experience, Resume


class ResumeLLM(Protocol):
    async def generate(self, model: str, job_posting: str, context: Dict[str, Any]) -> Resume:
        """Generate a resume for the supplied context."""


class InstructorLLM:
    """Instructor powered OpenAI client producing structured resumes."""

    def __init__(self, client: AsyncOpenAI | None = None) -> None:
        base_client = client or AsyncOpenAI()
        self.client = instructor.from_openai(base_client)

    async def generate(self, model: str, job_posting: str, context: Dict[str, Any]) -> Resume:
        prompt = self._build_prompt(job_posting, context)
        response = await self.client.chat.completions.create(
            model=model,
            response_model=Resume,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_retries=2,
        )
        response.metadata = {
            "model": model,
            "cached": False,
        }
        return response

    def _build_prompt(self, job_posting: str, context: Dict[str, Any]) -> str:
        formatted_context = json.dumps(context, indent=2, ensure_ascii=False)
        return (
            "You are an expert technical resume writer.\n"
            "Rules:\n"
            "1. Only use facts grounded in the provided context.\n"
            "2. Ensure every achievement is quantifiable with metrics.\n"
            "3. Mirror keywords from the job posting without keyword stuffing.\n"
            "4. Return data that matches the provided JSON schema.\n\n"
            f"Job Posting:\n{job_posting}\n\n"
            f"Context:\n{formatted_context}"
        )


class TemplateResumeLLM:
    """Deterministic fallback LLM that builds resumes from profile data."""

    def __init__(self) -> None:
        pass

    async def generate(self, model: str, job_posting: str, context: Dict[str, Any]) -> Resume:
        profile = context.get("profile", {})
        experiences = self._build_experiences(profile)
        resume = Resume(
            full_name=profile.get("full_name", "Taylor Candidate"),
            email=profile.get("email", "taylor@example.com"),
            phone=profile.get("phone", "+1 555-0100"),
            location=profile.get("location", "Remote"),
            summary=self._build_summary(job_posting, profile, experiences),
            experiences=experiences,
            education=profile.get("education", []),
            skills=profile.get("skills", []),
            citations={},
            confidence_scores={},
            metadata={"model": model, "cached": False},
        )
        # Provide naive citations grounding
        for exp in resume.experiences:
            for achievement in exp.achievements:
                resume.citations.setdefault(achievement, exp.company)
                resume.confidence_scores.setdefault(achievement, 0.85)
        resume.confidence_scores.setdefault("overall", 0.85)
        return resume

    def _build_experiences(self, profile: Dict[str, Any]) -> list[Experience]:
        experiences = []
        for entry in profile.get("experience", []):
            achievements = entry.get("achievements") or []
            if not achievements:
                achievements = ["Increased team efficiency by 10% through tooling improvements"]
            experience = Experience(
                company=entry.get("company", "Unknown Corp"),
                role=entry.get("role", "Professional"),
                start_date=entry.get("start_date"),
                end_date=entry.get("end_date"),
                achievements=achievements,
                location=entry.get("location"),
            )
            experiences.append(experience)
        if not experiences:
            experiences.append(
                Experience(
                    company="Sample Corp",
                    role="Engineer",
                    start_date=profile.get("start_date", "2020-01-01"),
                    end_date=None,
                    achievements=["Improved process efficiency by 15%"],
                    location=profile.get("location", "Remote"),
                )
            )
        return experiences

    def _build_summary(
        self, job_posting: str, profile: Dict[str, Any], experiences: Iterable[Experience]
    ) -> str:
        keywords = profile.get("skills", [])
        keyword_str = ", ".join(keywords[:5])
        years = profile.get("years_experience") or len(list(experiences)) * 2
        return (
            f"Results-driven professional with {years}+ years aligning experience to {job_posting[:60]} roles. "
            f"Skilled in {keyword_str} with a record of measurable impact."
        )[:500]


def resolve_ingestion_client() -> AsyncOpenAI | None:
    """Return an OpenAI client for ingestion flows when credentials exist."""

    if not os.getenv("OPENAI_API_KEY"):
        return None
    return AsyncOpenAI()


def resolve_llm() -> ResumeLLM:
    if os.getenv("OPENAI_API_KEY"):
        return InstructorLLM()
    return TemplateResumeLLM()
