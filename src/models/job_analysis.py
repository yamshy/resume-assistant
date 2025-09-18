"""Job analysis data models for the resume assistant.

This module contains pydantic models for job posting analysis results.
Models follow the specifications from specs/001-resume-tailoring-feature/data-model.md.
"""

from enum import Enum

from pydantic import BaseModel, Field

from models.profile import SkillCategory


class JobRequirement(BaseModel):
    """Individual job requirement with importance and category."""

    skill: str = Field(description="Required skill or qualification")
    importance: int = Field(ge=1, le=5, description="Importance level 1-5")
    category: SkillCategory = Field(description="Skill category")
    is_required: bool = Field(description="True if hard requirement, False if preferred")
    context: str = Field(description="Context where this requirement was mentioned")


class ResponsibilityLevel(str, Enum):
    """Job responsibility and seniority levels."""

    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"


class JobAnalysis(BaseModel):
    """Complete job analysis with requirements and company info."""

    company_name: str = Field(description="Company name")
    job_title: str = Field(description="Job title")
    department: str | None = Field(default=None, description="Department or team")
    location: str = Field(description="Job location")
    remote_policy: str | None = Field(default=None, description="Remote work policy")
    requirements: list[JobRequirement] = Field(description="Extracted job requirements")
    key_responsibilities: list[str] = Field(description="Main job responsibilities")
    company_culture: str = Field(description="Company culture description")
    role_level: ResponsibilityLevel = Field(description="Role seniority level")
    industry: str = Field(description="Industry sector")
    salary_range: str | None = Field(default=None, description="Salary range if mentioned")
    benefits: list[str] = Field(default=[], description="Benefits mentioned")
    preferred_qualifications: list[str] = Field(
        default=[], description="Nice-to-have qualifications"
    )
    analysis_timestamp: str = Field(description="When the analysis was completed")


__all__ = [
    "JobRequirement",
    "ResponsibilityLevel",
    "JobAnalysis",
]
