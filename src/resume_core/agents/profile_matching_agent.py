from __future__ import annotations

import json
from typing import Sequence

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.function import FunctionModel

from resume_core.models.job_analysis import JobAnalysis, JobRequirement
from resume_core.models.matching import ExperienceMatch, MatchingResult
from resume_core.models.profile import Skill, SkillCategory, UserProfile


class ProfileMatchingAgent:
    def __init__(self) -> None:
        self._agent = Agent(FunctionModel(self._run), name="profile-matching-agent")

    async def match(self, profile: UserProfile, analysis: JobAnalysis) -> MatchingResult:
        payload = {
            "profile": profile.model_dump(mode="json"),
            "analysis": analysis.model_dump(mode="json"),
        }
        result = await self._agent.run(json.dumps(payload))
        return MatchingResult.model_validate(json.loads(result.output))

    async def _run(
        self,
        messages: Sequence[ModelMessage],
        agent_info,  # noqa: ANN001
    ) -> ModelResponse:
        text = _extract_user_text(messages)
        payload = json.loads(text)
        profile = UserProfile.model_validate(payload["profile"])
        analysis = JobAnalysis.model_validate(payload["analysis"])
        matching = self._match(profile, analysis)
        return ModelResponse(parts=[TextPart(matching.model_dump_json())], model_name="function:profile-matching")

    def _match(self, profile: UserProfile, analysis: JobAnalysis) -> MatchingResult:
        result = MatchingResult(overall_match_score=0.0)
        keywords = profile.keyword_set()
        skill_lookup = {skill.name.lower(): skill for skill in profile.skills}

        for requirement in analysis.requirements:
            skill_lower = requirement.skill.lower()
            if skill_lower in keywords:
                skill_info = skill_lookup.get(skill_lower)
                proficiency = skill_info.proficiency if isinstance(skill_info, Skill) else 3
                evidence = _collect_evidence(profile, skill_lower)
                match_score = min(1.0, 0.6 + proficiency / 10)
                result.add_skill_match(
                    requirement.skill,
                    requirement.importance,
                    proficiency,
                    match_score,
                    evidence,
                )
                if evidence:
                    result.experience_matches.append(
                        ExperienceMatch(
                            job_responsibility=requirement.skill,
                            matching_experiences=evidence,
                            relevance_score=match_score,
                        )
                    )
            else:
                result.missing_requirements.append(JobRequirement.model_validate(requirement.model_dump()))

        result.compute_overall_score()
        result.strength_areas = [
            match.skill_name for match in result.skill_matches if match.match_score >= 0.75
        ]
        result.transferable_skills = _infer_transferable_skills(profile)
        result.recommendations = _build_recommendations(result)
        result.confidence_score = min(1.0, 0.7 + result.overall_match_score / 3)
        return result


def _extract_user_text(messages: Sequence[ModelMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, UserPromptPart):
                    return str(part.content)
    return ""


def _collect_evidence(profile: UserProfile, keyword: str) -> list[str]:
    keyword_lower = keyword.lower()
    evidence: set[str] = set()
    for experience in profile.experience:
        if any(keyword_lower in tech.lower() for tech in experience.technologies):
            evidence.add(f"{experience.position} at {experience.company}")
            continue
        for achievement in experience.achievements:
            if keyword_lower in achievement.lower():
                evidence.add(f"{experience.position} at {experience.company}")
    for project in profile.projects:
        if any(keyword_lower in tech.lower() for tech in project.technologies):
            evidence.add(project.name)
    return sorted(evidence)


def _infer_transferable_skills(profile: UserProfile) -> list[str]:
    soft_skills = [
        skill.name for skill in profile.skills if skill.category != SkillCategory.TECHNICAL
    ]
    return sorted(soft_skills)[:5]


def _build_recommendations(result: MatchingResult) -> list[str]:
    recommendations: list[str] = []
    if result.missing_requirements:
        missing = ", ".join(req.skill for req in result.missing_requirements)
        recommendations.append(f"Highlight training plans for: {missing}")
    if result.overall_match_score < 0.8:
        recommendations.append("Emphasize quantifiable impact in summary section")
    if not recommendations:
        recommendations.append("Profile strongly aligns with target role")
    return recommendations
