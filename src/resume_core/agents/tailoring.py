from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

from pydantic import TypeAdapter
from pydantic_ai import Agent as LlmAgent
from pydantic_ai.messages import ModelResponse, TextPart
from pydantic_ai.models.function import FunctionModel

from resume_core.models.job import JobAnalysis, JobRequirement, ResponsibilityLevel
from resume_core.models.matching import ExperienceMatch, MatchingResult, SkillMatch
from resume_core.models.profile import Skill, SkillCategory, UserProfile
from resume_core.models.resume import (
    ApprovalWorkflow,
    ResumeOptimization,
    TailoredResume,
    ValidationResult,
)


KNOWN_SKILLS = {
    "python": "Python",
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "postgresql": "PostgreSQL",
    "sql": "SQL",
    "aws": "AWS",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "leadership": "Leadership",
    "leading": "Leadership",
}


def _json_response(payload: Any) -> ModelResponse:
    def default_encoder(value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    return ModelResponse(parts=[TextPart(content=json.dumps(payload, default=default_encoder))])


def _latest_prompt(messages: list) -> str:
    # The `FunctionModel` passes ModelMessage instances. The last entry contains the
    # user prompt as the first part.
    return messages[-1].parts[0].content if messages and messages[-1].parts else ""


class JobAnalysisAgent:
    def __init__(self) -> None:
        def handler(messages, agent_info):  # type: ignore[override]
            description = _latest_prompt(messages)
            analysis = self._build_analysis(description)
            return _json_response(analysis.model_dump(mode="json"))

        self._adapter: TypeAdapter[JobAnalysis] = TypeAdapter(JobAnalysis)
        self._agent = LlmAgent(FunctionModel(handler), output_type=str)

    async def analyze(self, job_description: str) -> JobAnalysis:
        result = await self._agent.run(job_description)
        data = json.loads(result.output)
        return self._adapter.validate_python(data)

    def _build_analysis(self, description: str) -> JobAnalysis:
        lines = [line.strip() for line in description.splitlines()]
        non_empty = [line for line in lines if line]

        job_title = self._normalize_title(non_empty[0]) if non_empty else "Unknown Role"
        company = non_empty[1] if len(non_empty) > 1 else "Unknown Company"

        requirements: list[JobRequirement] = []
        preferred: list[str] = []
        in_preferred_section = False
        for raw_line in lines:
            if not raw_line:
                in_preferred_section = False
                continue
            lowered = raw_line.lower()
            if lowered.startswith("preferred qualifications"):
                in_preferred_section = True
                continue
            if lowered.startswith("preferred"):
                in_preferred_section = True
                preferred.append(raw_line.split(":", 1)[-1].strip())
                continue
            if raw_line.startswith(("-", "•")):
                batch = self._requirements_from_line(raw_line, preferred=in_preferred_section)
                requirements.extend(batch)
                if in_preferred_section:
                    preferred.append(raw_line.lstrip("-• ").strip())
                continue

        if not requirements:
            requirements.extend(self._keyword_requirements(description))

        role_level = self._infer_level(job_title)
        responsibilities = self._extract_responsibilities(description)
        culture = "collaborative environment" if re.search(r"team|collaborative", description, re.I) else "Not specified"
        remote_policy = "Remote friendly" if re.search(r"remote", description, re.I) else None

        return JobAnalysis(
            company_name=company,
            job_title=job_title,
            location=self._extract_location(description),
            remote_policy=remote_policy,
            requirements=requirements,
            key_responsibilities=responsibilities,
            company_culture=culture,
            role_level=role_level,
            industry="technology",
            benefits=self._extract_benefits(description),
            preferred_qualifications=[pref for pref in preferred if pref],
        )

    def _requirements_from_line(self, line: str, *, preferred: bool) -> list[JobRequirement]:
        text = line.lstrip("-• ")
        skill_names = self._extract_skill_names(text)
        if not skill_names:
            return [self._make_requirement(line, preferred=preferred)]

        importance = self._determine_importance(text, preferred=preferred)
        is_required = self._is_required(text, preferred=preferred)

        requirements = []
        for skill in skill_names:
            requirements.append(
                JobRequirement(
                    skill=skill,
                    importance=importance,
                    category=self._categorize_skill(skill),
                    is_required=is_required,
                    context=text,
                )
            )
        return requirements

    def _make_requirement(self, line: str, *, preferred: bool) -> JobRequirement:
        text = line.lstrip("-• ")
        skill_name = self._extract_skill_name(text)
        category = self._categorize_skill(skill_name)
        importance = self._determine_importance(text, preferred=preferred)
        is_required = self._is_required(text, preferred=preferred)
        return JobRequirement(
            skill=skill_name,
            importance=importance,
            category=category,
            is_required=is_required,
            context=text,
        )

    def _determine_importance(self, text: str, *, preferred: bool) -> int:
        if preferred:
            return 3
        if re.search(r"must|required", text, re.I):
            return 5
        if re.search(r"nice to have|preferred", text, re.I):
            return 3
        return 4

    def _is_required(self, text: str, *, preferred: bool) -> bool:
        if preferred:
            return False
        return not re.search(r"preferred|nice to have", text, re.I)

    def _normalize_title(self, line: str) -> str:
        for separator in [" wanted", " needed", " - ", " — ", ":", "|", " with ", " role", " position"]:
            if separator in line:
                return line.split(separator)[0].strip()
        return line.strip()

    def _extract_skill_name(self, text: str) -> str:
        lower = text.lower()
        for key, value in KNOWN_SKILLS.items():
            if re.search(rf"\b{re.escape(key)}\b", lower):
                return value
        cleaned = re.sub(r"[^a-zA-Z0-9 ]", "", text).strip()
        return cleaned.split()[0].title() if cleaned else "General Skill"

    def _extract_skill_names(self, text: str) -> list[str]:
        lower = text.lower()
        found: list[str] = []
        for key, value in KNOWN_SKILLS.items():
            if re.search(rf"\b{re.escape(key)}\b", lower) and value not in found:
                found.append(value)
        return found

    def _keyword_requirements(self, description: str) -> list[JobRequirement]:
        requirements: list[JobRequirement] = []
        lowered = description.lower()
        for key, value in KNOWN_SKILLS.items():
            if re.search(rf"\b{re.escape(key)}\b", lowered):
                requirements.append(
                    JobRequirement(
                        skill=value,
                        importance=4,
                        category=self._categorize_skill(value),
                        is_required=True,
                        context=f"Mentioned in description: {value}",
                    )
                )
        return requirements

    def _categorize_skill(self, skill: str) -> SkillCategory:
        technical = {"Python", "FastAPI", "Django", "Flask", "PostgreSQL", "SQL", "AWS", "Docker", "Kubernetes"}
        return SkillCategory.TECHNICAL if skill in technical else SkillCategory.SOFT

    def _infer_level(self, job_title: str) -> ResponsibilityLevel:
        lower = job_title.lower()
        if "intern" in lower or "junior" in lower:
            return ResponsibilityLevel.JUNIOR
        if "senior" in lower:
            return ResponsibilityLevel.SENIOR
        if "lead" in lower or "principal" in lower:
            return ResponsibilityLevel.LEAD
        if "director" in lower or "chief" in lower:
            return ResponsibilityLevel.EXECUTIVE
        return ResponsibilityLevel.MID

    def _extract_responsibilities(self, description: str) -> list[str]:
        responsibilities: list[str] = []
        for sentence in re.split(r"[.!]", description):
            sentence = sentence.strip()
            if not sentence:
                continue
            if re.search(r"build|design|lead|collaborate|deliver", sentence, re.I):
                responsibilities.append(sentence)
        return responsibilities[:5]

    def _extract_location(self, description: str) -> str:
        match = re.search(r"based in ([A-Za-z ,]+)", description)
        if match:
            return match.group(1).strip()
        return "Not specified"

    def _extract_benefits(self, description: str) -> list[str]:
        benefits: list[str] = []
        for line in description.splitlines():
            if re.search(r"benefits|health|vacation", line, re.I):
                benefits.append(line.strip())
        return benefits


class ProfileMatchingAgent:
    def __init__(self) -> None:
        def handler(messages, agent_info):  # type: ignore[override]
            payload = json.loads(_latest_prompt(messages))
            analysis = self._analysis_adapter.validate_python(payload["job_analysis"])
            profile = self._profile_adapter.validate_python(payload["profile"])
            matching = self._match_profile(analysis, profile)
            return _json_response(matching.model_dump(mode="json"))

        self._analysis_adapter: TypeAdapter[JobAnalysis] = TypeAdapter(JobAnalysis)
        self._profile_adapter: TypeAdapter[UserProfile] = TypeAdapter(UserProfile)
        self._adapter: TypeAdapter[MatchingResult] = TypeAdapter(MatchingResult)
        self._agent = LlmAgent(FunctionModel(handler), output_type=str)

    async def match(self, analysis: JobAnalysis, profile: UserProfile) -> MatchingResult:
        payload = {
            "job_analysis": analysis.model_dump(mode="json"),
            "profile": profile.model_dump(mode="json"),
        }
        result = await self._agent.run(json.dumps(payload))
        return self._adapter.validate_python(json.loads(result.output))

    def _match_profile(self, analysis: JobAnalysis, profile: UserProfile) -> MatchingResult:
        skill_map: dict[str, Skill] = {skill.name.lower(): skill for skill in profile.skills}
        skill_matches: list[SkillMatch] = []
        missing: list[JobRequirement] = []

        for requirement in analysis.requirements:
            key = requirement.skill.lower()
            skill = skill_map.get(key)
            if skill is None:
                missing.append(requirement)
                skill_matches.append(
                    SkillMatch(
                        skill_name=requirement.skill,
                        job_importance=requirement.importance,
                        user_proficiency=0,
                        match_score=0.0,
                        evidence=[],
                    )
                )
                continue

            evidence = self._gather_evidence(skill.name, profile)
            match_score = round(min(1.0, skill.proficiency / 5), 2)
            skill_matches.append(
                SkillMatch(
                    skill_name=skill.name,
                    job_importance=requirement.importance,
                    user_proficiency=skill.proficiency,
                    match_score=match_score,
                    evidence=evidence,
                )
            )

        experience_matches = self._match_responsibilities(analysis, profile)

        overall_score = 0.0
        if skill_matches:
            overall_score = round(sum(match.match_score for match in skill_matches) / len(skill_matches), 2)

        strength_areas = [match.skill_name for match in skill_matches if match.match_score >= 0.6]
        transferable_skills = [skill.name for skill in profile.skills if skill.name not in strength_areas]
        recommendations = self._build_recommendations(missing, analysis, profile, overall_score)

        return MatchingResult(
            overall_match_score=overall_score,
            skill_matches=skill_matches,
            experience_matches=experience_matches,
            missing_requirements=missing,
            strength_areas=strength_areas,
            transferable_skills=transferable_skills,
            recommendations=recommendations,
        )

    def _gather_evidence(self, skill_name: str, profile: UserProfile) -> list[str]:
        evidence: list[str] = []
        for experience in profile.experience:
            if any(skill_name.lower() in tech.lower() for tech in experience.technologies):
                evidence.append(
                    f"{experience.position} at {experience.company} using {skill_name}"
                )
            for achievement in experience.achievements:
                if skill_name.lower() in achievement.lower():
                    evidence.append(achievement)
        return evidence[:5]

    def _match_responsibilities(self, analysis: JobAnalysis, profile: UserProfile) -> list[ExperienceMatch]:
        matches: list[ExperienceMatch] = []
        for responsibility in analysis.key_responsibilities:
            related: list[str] = []
            for experience in profile.experience:
                if any(keyword in responsibility.lower() for keyword in self._keywords(experience)):
                    related.append(f"{experience.position} at {experience.company}")
            score = min(1.0, len(related) / max(1, len(profile.experience))) if related else 0.0
            matches.append(
                ExperienceMatch(
                    job_responsibility=responsibility,
                    matching_experiences=related,
                    relevance_score=round(score, 2),
                )
            )
        return matches

    def _keywords(self, experience: Any) -> Iterable[str]:
        keywords = set()
        for tech in experience.technologies:
            keywords.add(tech.lower())
        for achievement in experience.achievements:
            for word in achievement.split():
                keywords.add(word.lower().strip(",.()"))
        return keywords

    def _build_recommendations(
        self,
        missing: list[JobRequirement],
        analysis: JobAnalysis,
        profile: UserProfile,
        overall_score: float,
    ) -> list[str]:
        recommendations: list[str] = []
        for requirement in missing:
            recommendations.append(
                f"Provide concrete examples demonstrating {requirement.skill} experience."
            )

        if overall_score < 0.75:
            recommendations.append("Add measurable outcomes to highlight recent impact.")

        if not recommendations and analysis.key_responsibilities:
            primary_resp = analysis.key_responsibilities[0].rstrip(".")
            recommendations.append(
                f"Emphasize how your achievements cover {primary_resp.lower()}."
            )

        if not recommendations and profile.experience:
            latest_role = profile.experience[0]
            recommendations.append(
                f"Highlight leadership contributions from your role at {latest_role.company}."
            )

        return recommendations[:5]


class ResumeGenerationAgent:
    def __init__(self) -> None:
        def handler(messages, agent_info):  # type: ignore[override]
            payload = json.loads(_latest_prompt(messages))
            analysis = self._analysis_adapter.validate_python(payload["job_analysis"])
            profile = self._profile_adapter.validate_python(payload["profile"])
            matching = self._matching_adapter.validate_python(payload["matching_result"])
            preferences = payload.get("preferences") or {}
            timestamp = (
                datetime.fromisoformat(payload["timestamp"])
                if "timestamp" in payload
                else datetime.now(timezone.utc)
            )
            resume = self._generate_resume(analysis, matching, profile, preferences, timestamp)
            return _json_response(resume.model_dump(mode="json"))

        self._analysis_adapter: TypeAdapter[JobAnalysis] = TypeAdapter(JobAnalysis)
        self._profile_adapter: TypeAdapter[UserProfile] = TypeAdapter(UserProfile)
        self._matching_adapter: TypeAdapter[MatchingResult] = TypeAdapter(MatchingResult)
        self._adapter: TypeAdapter[TailoredResume] = TypeAdapter(TailoredResume)
        self._agent = LlmAgent(FunctionModel(handler), output_type=str)

    async def generate(
        self,
        analysis: JobAnalysis,
        matching: MatchingResult,
        profile: UserProfile,
        preferences: dict[str, Any],
        timestamp: datetime,
    ) -> TailoredResume:
        payload = {
            "job_analysis": analysis.model_dump(mode="json"),
            "matching_result": matching.model_dump(mode="json"),
            "profile": profile.model_dump(mode="json"),
            "preferences": preferences,
            "timestamp": timestamp.isoformat(),
        }
        result = await self._agent.run(json.dumps(payload))
        return self._adapter.validate_python(json.loads(result.output))

    def _generate_resume(
        self,
        analysis: JobAnalysis,
        matching: MatchingResult,
        profile: UserProfile,
        preferences: dict[str, Any],
        timestamp: datetime,
    ) -> TailoredResume:
        emphasis = [item.lower() for item in preferences.get("emphasis_areas", [])]
        excluded_sections = {
            str(section).replace("_", " ").strip().lower()
            for section in preferences.get("excluded_sections", [])
            if isinstance(section, str)
        }
        normalized_exclusions = set()
        for section in excluded_sections:
            if section in {"keymatches", "key match", "key-match"}:
                normalized_exclusions.add("key matches")
            else:
                normalized_exclusions.add(section)

        include_summary = "summary" not in normalized_exclusions
        base_summary = profile.professional_summary if include_summary else ""
        optimized_summary = (
            self._optimize_summary(base_summary, analysis, emphasis)
            if include_summary
            else ""
        )
        match_improvement = max(0.0, min(1.0, matching.overall_match_score + 0.1))

        optimizations: list[ResumeOptimization] = []
        if include_summary:
            optimizations.append(
                ResumeOptimization(
                    section="summary",
                    original_content=base_summary,
                    optimized_content=optimized_summary,
                    optimization_reason="Align summary with role title and key technologies",
                    keywords_added=[word for word in emphasis if word],
                    match_improvement=round(match_improvement, 2),
                )
            )

        markdown = self._compose_markdown(
            profile,
            analysis,
            optimized_summary,
            matching,
            normalized_exclusions,
        )

        change_notes: list[str] = []
        if include_summary:
            change_notes.append(
                "Updated summary to emphasize priority skills and leadership impact."
            )
        else:
            change_notes.append("Removed summary section per preferences.")
        if "experience" in normalized_exclusions:
            change_notes.append("Removed experience section per preferences.")
        if "key matches" in normalized_exclusions:
            change_notes.append("Removed key match diagnostics per preferences.")

        summary_of_changes = (
            " ".join(change_notes)
            if change_notes
            else "Applied requested preferences to tailored resume."
        )

        return TailoredResume(
            job_title=analysis.job_title,
            company_name=analysis.company_name,
            optimizations=optimizations,
            full_resume_markdown=markdown,
            summary_of_changes=summary_of_changes,
            estimated_match_score=round(match_improvement, 2),
            generation_timestamp=timestamp,
        )

    def _optimize_summary(
        self, summary: str, analysis: JobAnalysis, emphasis: list[str]
    ) -> str:
        highlights = ", ".join({skill.title() for skill in emphasis} or {"Python", "FastAPI"})
        base = f"Experienced {analysis.job_title} with proven results in {highlights}."
        if summary:
            return f"{base} {summary}" if not summary.startswith(base) else summary
        return base

    def _compose_markdown(
        self,
        profile: UserProfile,
        analysis: JobAnalysis,
        summary: str,
        matching: MatchingResult,
        excluded_sections: set[str],
    ) -> str:
        lines: list[str] = [f"# {profile.contact.name}", "", f"**{analysis.job_title}**", ""]

        if "summary" not in excluded_sections and summary:
            lines.append(summary)
            lines.append("")

        if "experience" not in excluded_sections and profile.experience:
            lines.append("## Experience")
            for exp in profile.experience:
                lines.append(f"### {exp.position} — {exp.company}")
                end_label = exp.end_date.strftime("%b %Y") if exp.end_date else "Present"
                lines.append(f"{exp.start_date:%b %Y} – {end_label}")
                lines.append(exp.description)
                for achievement in exp.achievements[:3]:
                    lines.append(f"- {achievement}")
                lines.append("")

        show_matches = "key matches" not in excluded_sections
        if show_matches and matching.skill_matches:
            lines.append("## Key Matches")
            for match in matching.skill_matches[:5]:
                lines.append(f"- {match.skill_name}: match score {match.match_score:.2f}")

        return "\n".join(lines)


class ValidationAgent:
    def __init__(self) -> None:
        def handler(messages, agent_info):  # type: ignore[override]
            payload = json.loads(_latest_prompt(messages))
            analysis = self._analysis_adapter.validate_python(payload["job_analysis"])
            matching = self._matching_adapter.validate_python(payload["matching_result"])
            resume = self._resume_adapter.validate_python(payload["tailored_resume"])
            result = self._validate_output(analysis, matching, resume)
            return _json_response(result.model_dump(mode="json"))

        self._analysis_adapter: TypeAdapter[JobAnalysis] = TypeAdapter(JobAnalysis)
        self._matching_adapter: TypeAdapter[MatchingResult] = TypeAdapter(MatchingResult)
        self._resume_adapter: TypeAdapter[TailoredResume] = TypeAdapter(TailoredResume)
        self._adapter: TypeAdapter[ValidationResult] = TypeAdapter(ValidationResult)
        self._agent = LlmAgent(FunctionModel(handler), output_type=str)

    async def validate(
        self,
        analysis: JobAnalysis,
        matching: MatchingResult,
        resume: TailoredResume,
    ) -> ValidationResult:
        payload = {
            "job_analysis": analysis.model_dump(mode="json"),
            "matching_result": matching.model_dump(mode="json"),
            "tailored_resume": resume.model_dump(mode="json"),
        }
        result = await self._agent.run(json.dumps(payload))
        return self._adapter.validate_python(json.loads(result.output))

    def _validate_output(
        self,
        analysis: JobAnalysis,
        matching: MatchingResult,
        resume: TailoredResume,
    ) -> ValidationResult:
        missing_penalty = len(matching.missing_requirements)
        accuracy = max(0.6, 1.0 - missing_penalty * 0.1)
        readability = max(0.7, min(0.95, len(resume.full_resume_markdown.split()) / 400))
        keyword_score = min(0.95, matching.overall_match_score + 0.1)
        overall = round((accuracy + readability + keyword_score) / 3, 2)
        timestamp = datetime.now(timezone.utc)
        strengths = [
            "Summary aligns with job title",
            "Key skills emphasized",
        ]
        issues = []
        if missing_penalty:
            issues.append("Some job requirements lack direct evidence")
        return ValidationResult(
            is_valid=accuracy > 0.75,
            accuracy_score=round(accuracy, 2),
            readability_score=round(readability, 2),
            keyword_optimization_score=round(keyword_score, 2),
            issues=issues,
            strengths=strengths,
            overall_quality_score=overall,
            validation_timestamp=timestamp,
        )


class HumanInterfaceAgent:
    def __init__(self) -> None:
        def handler(messages, agent_info):  # type: ignore[override]
            payload = json.loads(_latest_prompt(messages))
            matching = self._matching_adapter.validate_python(payload["matching_result"])
            validation = self._validation_adapter.validate_python(payload["validation_result"])
            workflow = self._evaluate_workflow(matching, validation)
            return _json_response(workflow.model_dump(mode="json"))

        self._matching_adapter: TypeAdapter[MatchingResult] = TypeAdapter(MatchingResult)
        self._validation_adapter: TypeAdapter[ValidationResult] = TypeAdapter(ValidationResult)
        self._adapter: TypeAdapter[ApprovalWorkflow] = TypeAdapter(ApprovalWorkflow)
        self._agent = LlmAgent(FunctionModel(handler), output_type=str)

    async def evaluate(
        self,
        matching: MatchingResult,
        validation: ValidationResult,
    ) -> ApprovalWorkflow:
        payload = {
            "matching_result": matching.model_dump(mode="json"),
            "validation_result": validation.model_dump(mode="json"),
        }
        result = await self._agent.run(json.dumps(payload))
        return self._adapter.validate_python(json.loads(result.output))

    def _evaluate_workflow(
        self,
        matching: MatchingResult,
        validation: ValidationResult,
    ) -> ApprovalWorkflow:
        requires_review = matching.overall_match_score < 0.6 or validation.accuracy_score < 0.8
        review_reasons: list[str] = []
        if matching.overall_match_score < 0.6:
            review_reasons.append("Overall match score below threshold")
        if validation.accuracy_score < 0.8:
            review_reasons.append("Validation accuracy requires confirmation")

        confidence = round((matching.overall_match_score + validation.overall_quality_score) / 2, 2)
        auto_approve = not requires_review and confidence >= 0.8

        return ApprovalWorkflow(
            requires_human_review=requires_review,
            review_reasons=review_reasons,
            confidence_score=confidence,
            auto_approve_eligible=auto_approve,
        )


@dataclass
class TailoringAgents:
    job_analysis: JobAnalysisAgent
    profile_matching: ProfileMatchingAgent
    resume_generation: ResumeGenerationAgent
    validation: ValidationAgent
    human_interface: HumanInterfaceAgent

    @classmethod
    def default(cls) -> "TailoringAgents":
        return cls(
            job_analysis=JobAnalysisAgent(),
            profile_matching=ProfileMatchingAgent(),
            resume_generation=ResumeGenerationAgent(),
            validation=ValidationAgent(),
            human_interface=HumanInterfaceAgent(),
        )

