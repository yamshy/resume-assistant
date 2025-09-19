"""Domain models used across the resume service."""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List, Optional
import re

from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator


def _ensure_metric(text: str) -> bool:
    """Check if text contains quantifiable evidence."""

    metric_keywords = ("%", "percent", "increase", "decrease", "improve", "growth")
    return bool(re.search(r"\d", text)) or any(keyword in text.lower() for keyword in metric_keywords)


class Experience(BaseModel):
    """Professional experience entry for a resume."""

    company: str = Field(..., min_length=1, max_length=100)
    role: str = Field(..., min_length=1, max_length=100)
    start_date: date
    end_date: Optional[date] = None
    achievements: List[str] = Field(..., min_length=1, max_length=8)
    location: Optional[str] = Field(default=None, max_length=100)

    @field_validator("achievements", mode="before")
    @classmethod
    def _strip_blank_achievements(cls, value: List[str]) -> List[str]:
        return [item.strip() for item in value if item and item.strip()]

    @field_validator("achievements")
    @classmethod
    def _validate_achievements(cls, value: List[str]) -> List[str]:
        for achievement in value:
            if not _ensure_metric(achievement):
                raise ValueError("Achievements should contain quantifiable metrics")
        return value

    @model_validator(mode="after")
    def _validate_dates(self) -> "Experience":
        if self.end_date and self.end_date < self.start_date:
            msg = "End date must be greater than or equal to start date"
            raise ValueError(msg)
        return self


class Education(BaseModel):
    """Education entry for the resume."""

    institution: str = Field(..., min_length=1, max_length=150)
    degree: str = Field(..., min_length=1, max_length=150)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    gpa: Optional[str] = Field(default=None, max_length=10)
    highlights: List[str] = Field(default_factory=list, max_length=5)


class Resume(BaseModel):
    """Strict schema for ATS compatible resume generation."""

    full_name: str = Field(..., min_length=3, max_length=120)
    email: EmailStr
    phone: str = Field(..., pattern=r"^[\+\d\s\-\(\)]+$", max_length=30)
    location: str = Field(..., min_length=2, max_length=120)
    summary: str = Field(..., min_length=50, max_length=500)
    experiences: List[Experience] = Field(..., min_length=1, max_length=10)
    education: List[Education] = Field(default_factory=list, max_length=5)
    skills: List[str] = Field(default_factory=list, max_length=20)
    citations: Dict[str, str] = Field(default_factory=dict)
    confidence_scores: Dict[str, float] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("skills", mode="before")
    @classmethod
    def _normalize_skills(cls, value: List[str]) -> List[str]:
        return [skill.strip() for skill in value if skill and skill.strip()]

    def to_text(self) -> str:
        """Convert resume to a deterministic ATS-friendly text representation."""

        lines = [self.full_name, self.email, self.phone, self.location, "", "Summary", self.summary]

        if self.skills:
            lines.extend(["", "Skills", ", ".join(self.skills)])

        if self.experiences:
            lines.append("")
            lines.append("Professional Experience")
            for exp in self.experiences:
                lines.append(f"{exp.role} | {exp.company} ({exp.start_date} - {exp.end_date or 'Present'})")
                if exp.location:
                    lines.append(exp.location)
                lines.extend(f"- {achievement}" for achievement in exp.achievements)

        if self.education:
            lines.append("")
            lines.append("Education")
            for edu in self.education:
                date_range = ""
                if edu.start_date or edu.end_date:
                    date_range = f" ({edu.start_date or ''} - {edu.end_date or 'Present'})"
                lines.append(f"{edu.degree} | {edu.institution}{date_range}")
                lines.extend(f"- {highlight}" for highlight in edu.highlights)
                if edu.gpa:
                    lines.append(f"GPA: {edu.gpa}")

        return "\n".join(lines).strip()
