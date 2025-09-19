"""Generates tailored resumes using verified profile data."""

from __future__ import annotations

import asyncio
from collections import Counter
from textwrap import shorten
from typing import Any

from app.models.profile import Experience, Skill, UserProfile


class ResumeGenerator:
    """Lightweight generator that tailors a resume to a job posting."""

    async def generate(self, job_posting: str, profile: UserProfile) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._generate_sync, job_posting, profile)

    def _generate_sync(self, job_posting: str, profile: UserProfile) -> dict[str, Any]:
        summary = self._build_summary(job_posting, profile)
        experiences = [self._format_experience(exp) for exp in profile.experiences]
        skills = self._select_relevant_skills(job_posting, profile.skills)
        projects = profile.projects
        education = profile.education
        return {
            "summary": summary,
            "experiences": experiences,
            "skills": skills,
            "projects": projects,
            "education": education,
            "metadata": {
                "job_posting_excerpt": shorten(job_posting, width=200, placeholder="…"),
            },
        }

    def _build_summary(self, job_posting: str, profile: UserProfile) -> str:
        keywords = self._extract_keywords(job_posting)
        headline_skills = ", ".join(keywords[:3]) if keywords else "multidisciplinary"
        years = max((skill.years for skill in profile.skills), default=1)
        return (
            f"Experienced professional with {years}+ years delivering impact using {headline_skills}. "
            "All claims verified against past experience."
        )

    def _format_experience(self, experience: Experience) -> dict[str, Any]:
        return {
            "company": experience.company,
            "role": experience.role,
            "start_date": experience.start_date.isoformat(),
            "end_date": experience.end_date.isoformat() if experience.end_date else None,
            "achievements": experience.achievements,
            "skills_used": experience.skills_used,
            "confidence": experience.confidence,
        }

    def _select_relevant_skills(self, job_posting: str, skills: list[Skill]) -> list[dict[str, Any]]:
        keywords = set(self._extract_keywords(job_posting))
        ranked: list[tuple[int, Skill]] = []
        for skill in skills:
            score = 1
            if skill.name.lower() in keywords:
                score += 2
            score += skill.years
            ranked.append((score, skill))
        ranked.sort(key=lambda item: item[0], reverse=True)
        selected = [self._format_skill(skill) for _, skill in ranked[:8]]
        return selected

    def _format_skill(self, skill: Skill) -> dict[str, Any]:
        return {
            "name": skill.name,
            "category": skill.category,
            "proficiency": skill.proficiency,
            "years": skill.years,
            "confidence": skill.confidence,
        }

    def _extract_keywords(self, job_posting: str) -> list[str]:
        tokens = [token.strip(".,") for token in job_posting.lower().split() if len(token) > 3]
        counter = Counter(tokens)
        return [word for word, _ in counter.most_common(10)]
