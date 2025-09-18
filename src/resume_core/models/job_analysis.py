from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from .profile import SkillCategory


class RoleLevel(str, Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"


class JobRequirement(BaseModel):
    skill: str
    importance: int = Field(ge=1, le=5)
    category: SkillCategory = SkillCategory.TECHNICAL
    is_required: bool = True
    context: str


class JobAnalysis(BaseModel):
    company_name: str
    job_title: str
    department: str | None = None
    location: str = "Not specified"
    remote_policy: str | None = None
    requirements: list[JobRequirement] = Field(default_factory=list)
    key_responsibilities: list[str] = Field(default_factory=list)
    company_culture: str = "collaborative environment"
    role_level: RoleLevel = RoleLevel.SENIOR
    industry: str = "technology"
    salary_range: str | None = None
    benefits: list[str] = Field(default_factory=list)
    preferred_qualifications: list[str] = Field(default_factory=list)
