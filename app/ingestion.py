"""Resume ingestion helpers for turning free-form resumes into structured data."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Iterable, Sequence

if TYPE_CHECKING:  # pragma: no cover - import used only for typing
    from instructor.client import Instructor
    from openai import AsyncOpenAI

    from .agents import AgentTool, ResumeIngestionAgent

from .llm import resolve_ingestion_client


@dataclass
class ParsedExperience:
    """Structured experience extracted from an uploaded resume."""

    company: str
    role: str
    achievements: list[str] = field(default_factory=list)
    start_date: str | None = None
    end_date: str | None = None
    location: str | None = None


@dataclass
class ParsedResume:
    """Parsed representation of a resume suitable for storage and generation."""

    source: str
    full_name: str | None
    email: str | None
    phone: str | None
    skills: list[str] = field(default_factory=list)
    experiences: list[ParsedExperience] = field(default_factory=list)

    def to_profile_fragment(self) -> dict:
        """Return a profile fragment that can be merged into the knowledge base."""

        return {
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "skills": self.skills,
            "experience": [
                {
                    "company": exp.company,
                    "role": exp.role,
                    "achievements": exp.achievements,
                }
                for exp in self.experiences
            ],
        }


class ResumeIngestor:
    """Thin wrapper around :class:`ResumeIngestionAgent` with normalised output."""

    def __init__(
        self,
        *,
        agent: "ResumeIngestionAgent" | None = None,
        client: AsyncOpenAI | Instructor | None = None,
        tools: dict[str, "AgentTool"] | None = None,
    ) -> None:
        if agent is not None:
            if tools is not None:
                raise ValueError("Specify either an agent or tools, not both.")
            if client is not None:
                raise ValueError("Provide either an agent or a client, not both.")
            self.agent = agent
            return

        from .agents import ResumeIngestionAgent, default_tool_registry

        registry = tools if tools is not None else default_tool_registry()
        resolved_client = client if client is not None else resolve_ingestion_client()
        self.agent = ResumeIngestionAgent(
            tool_registry=registry,
            client=resolved_client,
        )

    async def parse(self, source: str, text: str, notes: str | None = None) -> ParsedResume:
        """Parse a resume body into structured components via the ingestion agent."""

        result = await self.agent.ingest(source=source, text=text, notes=notes)
        return self._normalise(result, source, text)

    async def parse_many(
        self, payloads: Iterable[tuple[str, str]], notes: str | None = None
    ) -> list[ParsedResume]:
        """Parse multiple resumes sequentially."""

        parsed: list[ParsedResume] = []
        for source, text in payloads:
            parsed.append(await self.parse(source, text, notes))
        return parsed

    def _normalise(
        self, resume: ParsedResume | dict[str, Any], source: str, text: str
    ) -> ParsedResume:
        if isinstance(resume, ParsedResume):
            full_name = resume.full_name
            email = resume.email
            phone = resume.phone
            skills = list(resume.skills)
            experiences_input: Sequence[Any] = resume.experiences
        elif isinstance(resume, dict):
            full_name = resume.get("full_name")
            email = resume.get("email")
            phone = resume.get("phone")
            skills = list(resume.get("skills", []))
            experiences_input = resume.get("experiences", [])
        else:  # pragma: no cover - defensive guard for unexpected outputs
            raise TypeError("Unsupported resume payload from agent")
        experiences = self._coerce_experiences(experiences_input, text)
        skills = self._dedupe_skills(skills)
        return ParsedResume(
            source=source,
            full_name=full_name,
            email=email,
            phone=phone,
            skills=skills,
            experiences=experiences,
        )

    def _coerce_experiences(
        self, experiences: Sequence[Any], text: str
    ) -> list[ParsedExperience]:
        parsed: list[ParsedExperience] = []
        for entry in experiences:
            if isinstance(entry, ParsedExperience):
                parsed.append(
                    ParsedExperience(
                        company=entry.company,
                        role=entry.role,
                        achievements=list(entry.achievements),
                        start_date=entry.start_date,
                        end_date=entry.end_date,
                        location=entry.location,
                    )
                )
                continue
            if isinstance(entry, dict):
                achievements = [
                    str(achievement).strip()
                    for achievement in entry.get("achievements", [])
                    if str(achievement).strip()
                ]
                parsed.append(
                    ParsedExperience(
                        company=str(entry.get("company") or "Experience"),
                        role=str(entry.get("role") or "Professional"),
                        achievements=achievements,
                        start_date=entry.get("start_date"),
                        end_date=entry.get("end_date"),
                        location=entry.get("location"),
                    )
                )
                continue
        if parsed:
            return parsed
        summary = " ".join(line.strip() for line in text.splitlines() if line.strip())
        achievements = [summary[:240]] if summary else []
        return [
            ParsedExperience(
                company="Uploaded Resume",
                role="Professional",
                achievements=achievements,
            )
        ]

    def _dedupe_skills(self, skills: Sequence[str]) -> list[str]:
        deduped: list[str] = []
        seen: set[str] = set()
        for skill in skills:
            cleaned = skill.strip()
            if not cleaned:
                continue
            key = cleaned.lower()
            if key not in seen:
                seen.add(key)
                deduped.append(cleaned)
        return deduped
