"""Claim validation utilities."""

from __future__ import annotations

import asyncio
import re
from statistics import mean
from typing import Any

from app.models.profile import UserProfile
from app.models.resume import ValidationIssue, ValidationResult


SKILL_CLAIM_PATTERN = re.compile(r"(?P<years>\d+)\s+years? of (?P<skill>[A-Za-z +#]+) experience", re.IGNORECASE)


class ClaimValidator:
    """Validate generated resume content against the verified profile."""

    async def validate(self, resume: dict[str, Any], profile: UserProfile) -> ValidationResult:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._validate_sync, resume, profile)

    def _validate_sync(self, resume: dict[str, Any], profile: UserProfile) -> ValidationResult:
        issues: list[ValidationIssue] = []
        confidences: list[float] = []

        for skill_entry in resume.get("skills", []):
            name = str(skill_entry.get("name", "")).strip()
            if not name:
                continue
            score = self._score_skill(name, profile)
            confidences.append(score)
            if score < 0.75:
                issues.append(
                    ValidationIssue(
                        message=f"Skill {name} lacks verified evidence",
                        section="skills",
                        severity="high" if score < 0.5 else "medium",
                    )
                )

        for exp_entry in resume.get("experiences", []):
            role = exp_entry.get("role")
            company = exp_entry.get("company")
            score = self._score_experience(role, company, profile)
            confidences.append(score)
            if score < 0.7:
                issues.append(
                    ValidationIssue(
                        message=f"Experience {role} at {company} could not be verified",
                        section="experiences",
                        severity="high" if score < 0.4 else "medium",
                    )
                )

        overall_confidence = mean(confidences) if confidences else 1.0
        return ValidationResult(confidence=overall_confidence, issues=issues)

    async def validate_claim(self, claim: str, source_profile: dict[str, Any]) -> ValidationResult:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._validate_claim_sync, claim, source_profile)

    def _validate_claim_sync(self, claim: str, source_profile: dict[str, Any]) -> ValidationResult:
        match = SKILL_CLAIM_PATTERN.search(claim)
        if match:
            years = int(match.group("years"))
            skill = match.group("skill").strip().lower()
            skills = source_profile.get("skills", [])
            for candidate in skills:
                if candidate.get("name", "").lower() == skill and candidate.get("years", 0) >= years:
                    confidence = min(1.0, 0.7 + 0.05 * candidate.get("years", years))
                    return ValidationResult(confidence=confidence)
            return ValidationResult(
                confidence=0.3,
                issues=[
                    ValidationIssue(
                        message=f"No supporting evidence for {claim}",
                        section="skills",
                        severity="high",
                    )
                ],
            )
        # Default fallback for claims we cannot parse
        return ValidationResult(confidence=0.5)

    def _score_skill(self, name: str, profile: UserProfile) -> float:
        target = name.lower()
        for skill in profile.skills:
            if skill.name.lower() == target:
                return min(1.0, 0.6 + 0.05 * max(skill.years, 1))
        return 0.3

    def _score_experience(self, role: str | None, company: str | None, profile: UserProfile) -> float:
        if not role or not company:
            return 0.4
        role_lower = role.lower()
        company_lower = company.lower()
        for experience in profile.experiences:
            if experience.role.lower() == role_lower and experience.company.lower() == company_lower:
                return max(0.8, experience.confidence)
        return 0.35
