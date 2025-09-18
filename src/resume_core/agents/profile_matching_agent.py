from __future__ import annotations

from typing import Any

from resume_core.agents.base_agent import FunctionBackedAgent
from resume_core.models.job_analysis import JobAnalysis
from resume_core.models.matching import GapAnalysis, MatchingResult, SkillMatch
from resume_core.models.profile import UserProfile


class ProfileMatchingAgent(FunctionBackedAgent[MatchingResult]):
    def __init__(self) -> None:
        super().__init__(
            name="profile-matching-agent",
            instructions="Match job requirements to stored profile data and highlight strengths and gaps.",
            output_model=MatchingResult,
        )

    def build_output(self, payload: dict[str, Any]) -> MatchingResult:
        profile = UserProfile.model_validate(payload.get("profile") or {})
        analysis = JobAnalysis.model_validate(payload.get("analysis") or {})
        profile_keywords = self._collect_profile_keywords(profile)
        matches: list[SkillMatch] = []
        gaps: list[GapAnalysis] = []
        scores: list[float] = []

        for requirement in analysis.requirements:
            matched = [
                keyword
                for keyword in requirement.keywords
                if self._matches_keyword(keyword, profile_keywords)
            ]
            if matched:
                score = min(1.0, len(matched) / max(len(requirement.keywords), 1))
                scores.append(score)
                matches.append(
                    SkillMatch(
                        requirement=requirement.name,
                        matched_items=matched,
                        match_score=score,
                    )
                )
            else:
                scores.append(0.0)
                gaps.append(
                    GapAnalysis(
                        requirement=requirement.name,
                        missing_skills=requirement.keywords,
                    )
                )

        overall_score = round(sum(scores) / max(len(scores), 1), 2)
        recommendations = self._build_recommendations(matches, gaps)
        return MatchingResult(
            overall_score=overall_score,
            matched_skills=matches,
            gaps=gaps,
            recommendations=recommendations,
        )

    def _collect_profile_keywords(self, profile: UserProfile) -> set[str]:
        keywords: set[str] = set()
        if profile.summary:
            keywords.update(word.lower() for word in profile.summary.split())
        for skill in profile.skills:
            keywords.add(skill.name.lower())
            if skill.level:
                keywords.add(skill.level.lower())
        for experience in profile.experience:
            keywords.add(experience.role.lower())
            for skill in experience.skills:
                keywords.add(skill.lower())
            for achievement in experience.achievements:
                keywords.update(word.lower() for word in achievement.description.split())
        return keywords

    def _matches_keyword(self, keyword: str, keywords: set[str]) -> bool:
        normalized = keyword.lower()
        return normalized in keywords or any(normalized in value for value in keywords)

    def _build_recommendations(
        self, matches: list[SkillMatch], gaps: list[GapAnalysis]
    ) -> list[str]:
        recommendations: list[str] = []
        if matches:
            top_match = max(matches, key=lambda item: item.match_score)
            recommendations.append(
                f"Highlight {', '.join(sorted(top_match.matched_items))} in your summary."
            )
        for gap in gaps:
            recommendations.append(
                f"Prepare examples addressing {gap.requirement.lower()} requirements."
            )
        if not recommendations:
            recommendations.append("Profile aligns strongly with the role requirements.")
        return recommendations

    async def match(self, *, profile: UserProfile, analysis: JobAnalysis) -> MatchingResult:
        payload = {"profile": profile.model_dump(), "analysis": analysis.model_dump()}
        return await self.run(payload)
