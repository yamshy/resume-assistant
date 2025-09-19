"""Utilities for merging parsed resume data into a single profile."""

from __future__ import annotations

from collections import OrderedDict
from datetime import datetime, timezone
from typing import Iterable
from uuid import uuid4

from app.models.profile import Experience, Skill, UserProfile
from app.models.resume import ParsedResume


class Deduplicator:
    """Merge multiple parsed resumes into a single user profile."""

    async def merge(self, parsed_resumes: Iterable[ParsedResume]) -> UserProfile:
        experiences = self._merge_experiences(parsed_resumes)
        skills = self._merge_skills(parsed_resumes, experiences)
        education = self._merge_dict_sections(parsed_resumes, "education")
        projects = self._merge_dict_sections(parsed_resumes, "projects")
        now = datetime.now(timezone.utc)
        return UserProfile(
            id=uuid4(),
            experiences=experiences,
            skills=skills,
            education=education,
            projects=projects,
            created_at=now,
            updated_at=now,
        )

    def _merge_experiences(self, parsed_resumes: Iterable[ParsedResume]) -> list[Experience]:
        bucket: OrderedDict[tuple[str, str, str], Experience] = OrderedDict()
        for resume in parsed_resumes:
            for experience in resume.experiences:
                key = (
                    experience.company.lower(),
                    experience.role.lower(),
                    experience.start_date.isoformat(),
                )
                if key not in bucket:
                    bucket[key] = experience
                else:
                    existing = bucket[key]
                    existing.achievements = sorted(
                        {*(existing.achievements), *(experience.achievements)}
                    )
                    existing.skills_used = sorted({*(existing.skills_used), *(experience.skills_used)})
                    existing.confidence = max(existing.confidence, experience.confidence)
                    if experience.end_date and not existing.end_date:
                        existing.end_date = experience.end_date
        return list(bucket.values())

    def _merge_skills(
        self, parsed_resumes: Iterable[ParsedResume], experiences: list[Experience]
    ) -> list[Skill]:
        bucket: OrderedDict[str, Skill] = OrderedDict()
        for resume in parsed_resumes:
            for skill in resume.skills:
                key = skill.name.lower()
                if key not in bucket:
                    bucket[key] = skill
                else:
                    existing = bucket[key]
                    existing.years = max(existing.years, skill.years)
                    existing.confidence = max(existing.confidence, skill.confidence)
                    existing.evidence = list({*(existing.evidence), *(skill.evidence)})
        inferred = {skill for exp in experiences for skill in exp.skills_used}
        for name in inferred:
            key = name.lower()
            if key not in bucket:
                bucket[key] = Skill(name=name, category="experience", proficiency="advanced", years=1)
        return list(bucket.values())

    def _merge_dict_sections(
        self, parsed_resumes: Iterable[ParsedResume], attribute: str
    ) -> list[dict]:
        merged: list[dict] = []
        seen: set[tuple] = set()
        for resume in parsed_resumes:
            items = getattr(resume, attribute)
            for item in items:
                marker = tuple(sorted(item.items()))
                if marker not in seen:
                    seen.add(marker)
                    merged.append(item)
        return merged
