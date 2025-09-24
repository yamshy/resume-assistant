"""Persistence helpers for storing structured resume knowledge."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, cast

from .ingestion import ParsedResume


class KnowledgeStore:
    """Tiny JSON backed store that aggregates resumes into a unified profile."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, list[Any]] = {
            "resumes": [],
            "skills": [],
            "experiences": [],
        }
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return
        if isinstance(payload, dict):
            resumes = self._normalise_resumes(payload.get("resumes"))
            skills = self._normalise_skills(payload.get("skills"))
            experiences = self._normalise_experiences(payload.get("experiences"))
            self._data["resumes"] = cast(list[Any], resumes)
            self._data["skills"] = cast(list[Any], skills)
            self._data["experiences"] = cast(list[Any], experiences)

    def _persist(self) -> None:
        serialisable = {
            "resumes": self._data["resumes"],
            "skills": sorted(set(self._data["skills"]), key=str.lower),
            "experiences": self._data["experiences"],
        }
        self.path.write_text(json.dumps(serialisable, indent=2, ensure_ascii=False), encoding="utf-8")

    def add_resumes(self, resumes: Iterable[ParsedResume]) -> dict:
        """Add parsed resumes to the store, returning a summary of new knowledge."""

        new_skills: set[str] = set()
        new_achievements = 0
        for resume in resumes:
            self._append_identity(resume)
            new_skills.update(self._append_skills(resume.skills))
            new_achievements += self._append_experiences(resume)
        self._persist()
        return {
            "skills_added": sorted(new_skills, key=str.lower),
            "achievements_indexed": new_achievements,
            "profile_snapshot": self.aggregated_profile() or {},
        }

    def _append_identity(self, resume: ParsedResume) -> None:
        identity = {
            "source": resume.source,
            "full_name": resume.full_name,
            "email": resume.email,
            "phone": resume.phone,
        }
        self._data.setdefault("resumes", []).append(identity)

    def _append_skills(self, skills: Iterable[str]) -> set[str]:
        skills_list = self._normalise_skills(self._data.get("skills"))
        self._data["skills"] = cast(list[Any], skills_list)
        incoming = self._normalise_skills(skills)
        existing_keys = {skill.lower() for skill in skills_list}
        added: set[str] = set()
        for skill in incoming:
            key = skill.lower()
            if key not in existing_keys:
                existing_keys.add(key)
                skills_list.append(skill)
                added.add(skill)
        return added

    def _append_experiences(self, resume: ParsedResume) -> int:
        stored = self._normalise_experiences(self._data.get("experiences"))
        self._data["experiences"] = cast(list[Any], stored)
        count = 0
        for experience in resume.experiences:
            start_date = experience.start_date or self._fallback_start_date(len(stored))
            payload = {
                "source": resume.source,
                "company": experience.company,
                "role": experience.role,
                "achievements": experience.achievements,
                "start_date": start_date,
                "end_date": experience.end_date,
                "location": experience.location,
            }
            stored.append(payload)
            count += len(experience.achievements)
        return count

    def aggregated_profile(self) -> dict | None:
        """Return a consolidated profile built from all stored resumes."""

        if not self._data.get("skills") and not self._data.get("experiences"):
            return None
        full_name = self._select_most_common("full_name")
        email = self._select_most_common("email")
        phone = self._select_most_common("phone")
        experiences: list[dict] = []
        for index, entry in enumerate(self._data.get("experiences", [])):
            start_date = entry.get("start_date") or self._fallback_start_date(index)
            experiences.append(
                {
                    "company": entry.get("company") or "Experience",
                    "role": entry.get("role") or "Professional",
                    "achievements": entry.get("achievements", []),
                    "start_date": start_date,
                    "end_date": entry.get("end_date"),
                    "location": entry.get("location") or "Remote",
                }
            )
        years_experience = max(len(experiences) * 2, 2) if experiences else 2
        return {
            "full_name": full_name or "Resume Candidate",
            "email": email or "candidate@example.com",
            "phone": phone or "+1 555-0100",
            "skills": sorted(set(self._data.get("skills", [])), key=str.lower),
            "experience": experiences,
            "years_experience": years_experience,
        }

    def _fallback_start_date(self, index: int) -> str:
        base_year = 2020
        year = max(2000, base_year - index * 2)
        return f"{year}-01-01"

    def _select_most_common(self, field: str) -> str | None:
        values = [entry.get(field) for entry in self._data.get("resumes", []) if entry.get(field)]
        if not values:
            return None
        tally = Counter(values)
        most_common = tally.most_common(1)
        return most_common[0][0] if most_common else None

    def _normalise_resumes(self, resumes: Any) -> list[dict[str, Any]]:
        if isinstance(resumes, dict):
            candidates: Iterable[Any] = [resumes]
        elif isinstance(resumes, list):
            candidates = resumes
        elif isinstance(resumes, Iterable) and not isinstance(resumes, (str, bytes)):
            candidates = list(resumes)
        else:
            return []
        return [entry for entry in candidates if isinstance(entry, dict)]

    def _normalise_skills(self, skills: Any) -> list[str]:
        if skills is None:
            return []
        if isinstance(skills, str):
            candidates: Iterable[Any] = [skills]
        elif isinstance(skills, list):
            candidates = skills
        elif isinstance(skills, Iterable) and not isinstance(skills, (str, bytes, dict)):
            candidates = list(skills)
        else:
            return []
        normalised: list[str] = []
        for skill in candidates:
            if isinstance(skill, str):
                stripped = skill.strip()
                if stripped:
                    normalised.append(stripped)
        return normalised

    def _normalise_experiences(self, experiences: Any) -> list[dict[str, Any]]:
        if isinstance(experiences, dict):
            candidates: Iterable[Any] = [experiences]
        elif isinstance(experiences, list):
            candidates = experiences
        elif isinstance(experiences, Iterable) and not isinstance(experiences, (str, bytes)):
            candidates = list(experiences)
        else:
            return []
        normalised: list[dict[str, Any]] = []
        for entry in candidates:
            if not isinstance(entry, dict):
                continue
            cleaned = dict(entry)
            cleaned["achievements"] = self._normalise_skills(cleaned.get("achievements"))
            normalised.append(cleaned)
        return normalised
