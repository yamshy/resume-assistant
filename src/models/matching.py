"""
Profile matching result data models.

Based on data-model.md specification for Profile Matching Agent output.
"""

from pydantic import BaseModel, Field

from models.job_analysis import JobRequirement

__all__ = ["SkillMatch", "ExperienceMatch", "MatchingResult"]


class SkillMatch(BaseModel):
    skill_name: str = Field(description="Skill name")
    job_importance: int = Field(ge=1, le=5, description="Importance in job posting")
    user_proficiency: int = Field(ge=0, le=5, description="User proficiency (0 if not found)")
    match_score: float = Field(ge=0, le=1, description="Match score 0-1")
    evidence: list[str] = Field(description="Evidence from user profile")


class ExperienceMatch(BaseModel):
    job_responsibility: str = Field(description="Job responsibility")
    matching_experiences: list[str] = Field(description="Matching user experiences")
    relevance_score: float = Field(ge=0, le=1, description="Relevance score 0-1")


class MatchingResult(BaseModel):
    overall_match_score: float = Field(ge=0, le=1, description="Overall match score")
    skill_matches: list[SkillMatch] = Field(description="Individual skill match details")
    experience_matches: list[ExperienceMatch] = Field(description="Experience alignment details")
    missing_requirements: list[JobRequirement] = Field(description="Requirements user doesn't meet")
    strength_areas: list[str] = Field(description="Areas where user exceeds requirements")
    transferable_skills: list[str] = Field(
        description="Skills that could transfer to missing areas"
    )
    recommendations: list[str] = Field(description="Specific improvement recommendations")
    confidence_score: float = Field(ge=0, le=1, description="Confidence in analysis")
