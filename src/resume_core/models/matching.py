from __future__ import annotations

from pydantic import BaseModel, Field


class SkillMatch(BaseModel):
    requirement: str
    matched_items: list[str] = Field(default_factory=list)
    match_score: float = 0.0


class GapAnalysis(BaseModel):
    requirement: str
    missing_skills: list[str] = Field(default_factory=list)


class MatchingResult(BaseModel):
    overall_score: float
    matched_skills: list[SkillMatch] = Field(default_factory=list)
    gaps: list[GapAnalysis] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
