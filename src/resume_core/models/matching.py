from __future__ import annotations

from pydantic import BaseModel, Field

from .job_analysis import JobRequirement


class SkillMatch(BaseModel):
    skill_name: str
    job_importance: int = Field(ge=1, le=5)
    user_proficiency: int = Field(ge=0, le=5)
    match_score: float = Field(ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list)


class ExperienceMatch(BaseModel):
    job_responsibility: str
    matching_experiences: list[str] = Field(default_factory=list)
    relevance_score: float = Field(ge=0.0, le=1.0)


class MatchingResult(BaseModel):
    overall_match_score: float = Field(ge=0.0, le=1.0)
    skill_matches: list[SkillMatch] = Field(default_factory=list)
    experience_matches: list[ExperienceMatch] = Field(default_factory=list)
    missing_requirements: list[JobRequirement] = Field(default_factory=list)
    strength_areas: list[str] = Field(default_factory=list)
    transferable_skills: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)

    def add_skill_match(
        self,
        skill_name: str,
        importance: int,
        user_proficiency: int,
        match_score: float,
        evidence: list[str],
    ) -> None:
        self.skill_matches.append(
            SkillMatch(
                skill_name=skill_name,
                job_importance=importance,
                user_proficiency=user_proficiency,
                match_score=min(1.0, max(0.0, match_score)),
                evidence=sorted(set(evidence)),
            )
        )

    def compute_overall_score(self) -> None:
        if not self.skill_matches:
            self.overall_match_score = 0.0
            return
        total = sum(match.match_score for match in self.skill_matches)
        self.overall_match_score = round(total / len(self.skill_matches), 2)
