"""Resume ingestion helpers for turning free-form resumes into structured data."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Iterable, Sequence

from .ingestion_utils import coerce_experiences, dedupe_skills

if TYPE_CHECKING:  # pragma: no cover - import used only for typing
    from .agents import ResumeIngestionAgent


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

    def __init__(self, agent: "ResumeIngestionAgent") -> None:
        self.agent = agent

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
        experiences = coerce_experiences(experiences_input, text)
        skills = dedupe_skills(skills)
        return ParsedResume(
            source=source,
            full_name=full_name,
            email=email,
            phone=phone,
            skills=skills,
            experiences=experiences,
        )

