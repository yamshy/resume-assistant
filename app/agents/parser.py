"""Simple resume parser used to bootstrap structured data."""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from typing import Iterable
from uuid import uuid4

from app.models.profile import Experience, Skill
from app.models.resume import ParsedResume


DATE_PATTERN = re.compile(r"(?:19|20)\d{2}")


class ResumeParser:
    """Parse plain text resumes into structured sections."""

    async def parse(self, resume_bytes: bytes) -> ParsedResume:
        loop = asyncio.get_running_loop()
        text = await loop.run_in_executor(None, self._decode, resume_bytes)
        experiences = self._parse_experiences(text)
        skills = self._parse_skills(text, experiences)
        education = self._extract_section(text, "education")
        projects = self._extract_section(text, "projects")
        return ParsedResume(
            experiences=experiences,
            skills=skills,
            education=[{"details": line} for line in education],
            projects=[{"details": line} for line in projects],
            source_name="uploaded_resume",
        )

    def _decode(self, payload: bytes) -> str:
        return payload.decode("utf-8", errors="ignore")

    def _extract_section(self, text: str, header: str) -> list[str]:
        lines = text.splitlines()
        capture = False
        captured: list[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                if capture:
                    break
                continue
            if stripped.lower().startswith(header.lower()):
                capture = True
                after_colon = stripped.split(":", 1)[1] if ":" in stripped else ""
                if after_colon.strip():
                    captured.append(after_colon.strip())
                continue
            if capture and ":" in stripped and stripped.lower().split(":", 1)[0].isalpha():
                break
            if capture:
                captured.append(stripped)
        return captured

    def _parse_experiences(self, text: str) -> list[Experience]:
        lines = self._extract_section(text, "experience")
        experiences: list[Experience] = []
        for line in lines:
            if not line:
                continue
            header, description = self._split_description(line)
            company, role = self._parse_company_role(header)
            start_date, end_date = self._parse_dates(header)
            achievements = self._split_achievements(description)
            skills_used = self._infer_skills_from_achievements(achievements)
            confidence = 0.9 if company and role else 0.6
            experiences.append(
                Experience(
                    id=uuid4(),
                    company=company or "Unknown Company",
                    role=role or "Unknown Role",
                    start_date=start_date,
                    end_date=end_date,
                    description=description,
                    achievements=achievements,
                    skills_used=skills_used,
                    confidence=confidence,
                )
            )
        if not experiences:
            fallback_description = text.strip().splitlines()[0] if text.strip() else "General experience"
            experiences.append(
                Experience(
                    id=uuid4(),
                    company="Unknown Company",
                    role="Professional",
                    start_date=datetime.now(timezone.utc),
                    end_date=None,
                    description=fallback_description,
                    achievements=[],
                    skills_used=[],
                    confidence=0.4,
                )
            )
        return experiences

    def _split_description(self, line: str) -> tuple[str, str]:
        if ":" in line:
            header, description = line.split(":", 1)
            return header.strip(), description.strip()
        return line.strip(), ""

    def _parse_company_role(self, header: str) -> tuple[str, str]:
        parts = [part.strip() for part in header.split("-") if part.strip()]
        if len(parts) >= 2:
            return parts[0], parts[1]
        return header.strip(), ""

    def _parse_dates(self, header: str) -> tuple[datetime, datetime | None]:
        matches = DATE_PATTERN.findall(header)
        now = datetime.now(timezone.utc)
        if not matches:
            return now.replace(month=1, day=1), None
        start_year = int(matches[0])
        start = datetime(year=start_year, month=1, day=1)
        end: datetime | None = None
        if len(matches) > 1:
            end_year = int(matches[1])
            end = datetime(year=end_year, month=1, day=1)
        return start, end

    def _split_achievements(self, description: str) -> list[str]:
        if not description:
            return []
        return [part.strip() for part in re.split(r"[;•]", description) if part.strip()]

    def _infer_skills_from_achievements(self, achievements: Iterable[str]) -> list[str]:
        skills = set()
        for achievement in achievements:
            for token in achievement.split():
                clean = re.sub(r"[^a-zA-Z]", "", token).lower()
                if clean in {"python", "fastapi", "sql", "aws", "docker"}:
                    skills.add(clean.capitalize())
        return sorted(skills)

    def _parse_skills(self, text: str, experiences: list[Experience]) -> list[Skill]:
        lines = self._extract_section(text, "skills")
        if not lines:
            inferred = {skill for exp in experiences for skill in exp.skills_used}
            return [self._build_skill(name) for name in inferred]
        skill_names = set()
        for line in lines:
            for token in re.split(r"[,/]| and ", line):
                name = token.strip()
                if name:
                    skill_names.add(name)
        return [self._build_skill(name) for name in sorted(skill_names)]

    def _build_skill(self, name: str) -> Skill:
        return Skill(name=name, proficiency="advanced" if len(name) < 15 else "intermediate", years=1)
