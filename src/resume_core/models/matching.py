from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict, Field

from .job import JobRequirement


class SkillMatch(BaseModel):
    model_config = ConfigDict(extra="ignore")

    skill_name: str
    job_importance: int
    user_proficiency: int
    match_score: float = Field(ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)


class ExperienceMatch(BaseModel):
    model_config = ConfigDict(extra="ignore")

    job_responsibility: str
    matching_experiences: List[str] = Field(default_factory=list)
    relevance_score: float = Field(ge=0.0, le=1.0)


class MatchingResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    overall_match_score: float = Field(ge=0.0, le=1.0)
    skill_matches: List[SkillMatch] = Field(default_factory=list)
    experience_matches: List[ExperienceMatch] = Field(default_factory=list)
    missing_requirements: List[JobRequirement] = Field(default_factory=list)
    strength_areas: List[str] = Field(default_factory=list)
    transferable_skills: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)

