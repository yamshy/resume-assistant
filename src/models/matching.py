"""
Profile matching result data models.

Based on data-model.md specification for Profile Matching Agent output.
"""
from pydantic import BaseModel, Field
from typing import List
from models.job_analysis import JobRequirement


__all__ = ["SkillMatch", "ExperienceMatch", "MatchingResult"]


class SkillMatch(BaseModel):
    skill_name: str = Field(description="Skill name")
    job_importance: int = Field(ge=1, le=5, description="Importance in job posting")
    user_proficiency: int = Field(ge=0, le=5, description="User proficiency (0 if not found)")
    match_score: float = Field(ge=0, le=1, description="Match score 0-1")
    evidence: List[str] = Field(description="Evidence from user profile")


class ExperienceMatch(BaseModel):
    job_responsibility: str = Field(description="Job responsibility")
    matching_experiences: List[str] = Field(description="Matching user experiences")
    relevance_score: float = Field(ge=0, le=1, description="Relevance score 0-1")


class MatchingResult(BaseModel):
    overall_match_score: float = Field(ge=0, le=1, description="Overall match score")
    skill_matches: List[SkillMatch] = Field(description="Individual skill match details")
    experience_matches: List[ExperienceMatch] = Field(description="Experience alignment details")
    missing_requirements: List[JobRequirement] = Field(description="Requirements user doesn't meet")
    strength_areas: List[str] = Field(description="Areas where user exceeds requirements")
    transferable_skills: List[str] = Field(description="Skills that could transfer to missing areas")
    recommendations: List[str] = Field(description="Specific improvement recommendations")
    confidence_score: float = Field(ge=0, le=1, description="Confidence in analysis")