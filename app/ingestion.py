"""Resume ingestion helpers for turning free-form resumes into structured data."""

from __future__ import annotations

import re
from dataclasses import dataclass, field


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
    """Utility that applies deterministic heuristics to extract resume structure."""

    SKILL_HEADINGS = ("skill", "technology", "stack", "tool", "competenc")
    ROLE_KEYWORDS = (
        "engineer",
        "developer",
        "manager",
        "lead",
        "director",
        "architect",
        "consultant",
        "specialist",
        "analyst",
        "scientist",
        "designer",
    )

    def parse(self, source: str, text: str, notes: str | None = None) -> ParsedResume:
        """Parse a resume body into structured components."""

        cleaned = text.replace("\r\n", "\n")
        full_name = self._extract_full_name(cleaned)
        email = self._extract_email(cleaned)
        phone = self._extract_phone(cleaned)
        skills = self._extract_skills(cleaned)
        experiences = self._extract_experiences(cleaned)

        return ParsedResume(
            source=source,
            full_name=full_name,
            email=email,
            phone=phone,
            skills=skills,
            experiences=experiences,
        )

    def _extract_full_name(self, text: str) -> str | None:
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines:
            if "@" in line or line.lower().startswith("linkedin"):
                continue
            words = line.split()
            if 1 < len(words) <= 5:
                capitalised = sum(1 for word in words if word and word[0].isupper())
                if capitalised >= max(2, len(words) - 1):
                    return line
        return lines[0] if lines else None

    def _extract_email(self, text: str) -> str | None:
        match = re.search(r"[\w.+-]+@[\w.-]+", text)
        return match.group(0) if match else None

    def _extract_phone(self, text: str) -> str | None:
        match = re.search(r"\+?\d[\d\s().-]{6,}\d", text)
        return match.group(0) if match else None

    def _extract_skills(self, text: str) -> list[str]:
        skills: list[str] = []
        lines = text.split("\n")
        for line in lines:
            lower = line.lower()
            if any(heading in lower for heading in self.SKILL_HEADINGS):
                _, _, trailing = line.partition(":")
                candidates = trailing if trailing else line
                skills.extend(self._split_skills(candidates))
        if not skills:
            # fall back to extracting capitalised tokens that look like tools
            tokens = re.findall(r"[A-Z]{2,}(?:[+#0-9]*)", text)
            skills.extend(token.strip() for token in tokens if len(token) > 2)
        normalised = []
        seen = set()
        for skill in skills:
            cleaned = skill.strip()
            if not cleaned:
                continue
            key = cleaned.lower()
            if key not in seen:
                seen.add(key)
                normalised.append(cleaned)
        return normalised

    def _split_skills(self, text: str) -> list[str]:
        return [token.strip() for token in re.split(r"[,/|•]\s*", text) if token.strip()]

    def _extract_experiences(self, text: str) -> list[ParsedExperience]:
        experiences: list[ParsedExperience] = []
        current: ParsedExperience | None = None
        lines = text.split("\n")
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if self._looks_like_role_heading(stripped):
                if current:
                    experiences.append(current)
                company, role = self._split_heading(stripped)
                current = ParsedExperience(company=company, role=role, achievements=[])
                continue
            bullet_match = re.match(r"^[•\-*]+\s*(.+)", stripped)
            if bullet_match:
                achievement = bullet_match.group(1).strip()
                if not achievement:
                    continue
                if current is None:
                    current = ParsedExperience(
                        company="Experience",
                        role="Professional",  # generic fallback
                        achievements=[achievement],
                    )
                else:
                    current.achievements.append(achievement)
                continue
            if re.search(r"\b(improv|reduc|increas|launch|deliver|own|build|design)\w*", stripped, re.I):
                if current is None:
                    current = ParsedExperience(company="Experience", role="Professional", achievements=[])
                current.achievements.append(stripped)
        if current:
            experiences.append(current)
        if not experiences:
            # Provide a single experience wrapper so downstream systems have context.
            summary = " ".join(line.strip() for line in lines if line.strip())
            achievements = [summary[:240]] if summary else []
            experiences.append(
                ParsedExperience(
                    company="Uploaded Resume",
                    role="Professional",
                    achievements=achievements,
                )
            )
        return experiences

    def _looks_like_role_heading(self, text: str) -> bool:
        lowered = text.lower()
        return any(keyword in lowered for keyword in self.ROLE_KEYWORDS)

    def _split_heading(self, text: str) -> tuple[str, str]:
        separators = [" at ", " - ", " | "]
        for separator in separators:
            if separator in text:
                company, role = text.split(separator, 1)
                return company.strip(), role.strip()
        parts = text.split()
        if len(parts) >= 2:
            return " ".join(parts[-1:]), " ".join(parts[:-1])
        return "Experience", text.strip()
