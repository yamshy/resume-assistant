from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from resume_core.agents.base_agent import FunctionBackedAgent
from resume_core.models.job_analysis import JobAnalysis
from resume_core.models.matching import MatchingResult
from resume_core.models.profile import UserProfile
from resume_core.models.resume import ContentOptimization, ResumeSection, TailoredResume


class ResumeGenerationAgent(FunctionBackedAgent[TailoredResume]):
    def __init__(self) -> None:
        super().__init__(
            name="resume-generation-agent",
            instructions="Generate a resume draft tailored to the provided job analysis and profile data.",
            output_model=TailoredResume,
        )

    def build_output(self, payload: dict[str, Any]) -> TailoredResume:
        profile = UserProfile.model_validate(payload.get("profile") or {})
        analysis = JobAnalysis.model_validate(payload.get("analysis") or {})
        matching = MatchingResult.model_validate(payload.get("matching") or {})

        job_title = analysis.context.role or "Tailored Resume"
        matched_keywords = {
            item for match in matching.matched_skills for item in match.matched_items
        }
        summary = self._compose_summary(profile.summary, matched_keywords, job_title)
        sections = self._build_sections(profile, matched_keywords)
        markdown = self._compose_markdown(profile, job_title, summary, sections, matched_keywords)
        optimization = ContentOptimization(
            focus_keywords=sorted(matched_keywords)[:10],
            readability_score=0.78 if summary else 0.65,
            action_verbs_used=["Led", "Delivered", "Optimized"],
        )
        return TailoredResume(
            resume_id=str(uuid4()),
            job_title=job_title,
            summary=summary,
            sections=sections,
            markdown=markdown,
            created_at=datetime.now(UTC),
            optimization=optimization,
            metadata={"matched_keywords": sorted(matched_keywords)},
        )

    def _compose_summary(
        self, profile_summary: str, matched_keywords: set[str], job_title: str
    ) -> str:
        highlights = (
            ", ".join(sorted(matched_keywords)) if matched_keywords else "impactful outcomes"
        )
        if profile_summary:
            return f"{profile_summary.strip()} Tailored for a {job_title} role with emphasis on {highlights}."
        return f"Experienced professional tailored for {job_title} opportunities with focus on {highlights}."

    def _build_sections(
        self, profile: UserProfile, matched_keywords: set[str]
    ) -> list[ResumeSection]:
        experience_lines: list[str] = []
        for experience in profile.experience:
            period = f"{experience.start_date} – {experience.end_date or 'Present'}"
            experience_lines.append(f"### {experience.role} · {experience.company}")
            experience_lines.append(period)
            for achievement in experience.achievements:
                experience_lines.append(f"- {achievement.description}")
            if experience.skills:
                highlight = ", ".join(experience.skills)
                experience_lines.append(f"- Tools: {highlight}")
            experience_lines.append("")
        skills_lines = ["- " + skill.name for skill in profile.skills] or ["- Add specific skills"]
        if matched_keywords:
            skills_lines.append("- Focus: " + ", ".join(sorted(matched_keywords)))
        sections = [
            ResumeSection(title="Professional Summary", content=profile.summary or ""),
            ResumeSection(title="Experience", content="\n".join(experience_lines).strip()),
            ResumeSection(title="Skills", content="\n".join(skills_lines).strip()),
        ]
        return sections

    def _compose_markdown(
        self,
        profile: UserProfile,
        job_title: str,
        summary: str,
        sections: list[ResumeSection],
        matched_keywords: set[str],
    ) -> str:
        contact = profile.contact
        header_name = contact.name or "Candidate"
        lines: list[str] = [f"# {header_name}"]
        contact_bits = [contact.email, contact.phone, contact.location]
        contact_line = " | ".join(bit for bit in contact_bits if bit)
        if contact_line:
            lines.append(contact_line)
        lines.append("")
        lines.append(f"**{job_title}**")
        lines.append("")
        lines.append(summary)
        lines.append("")
        for section in sections:
            if section.content:
                lines.append(f"## {section.title}")
                lines.append(section.content)
                lines.append("")
        if matched_keywords:
            lines.append("## Keywords for ATS")
            lines.append(", ".join(sorted(matched_keywords)))
            lines.append("")
        return "\n".join(line for line in lines if line is not None).strip()

    async def generate(
        self,
        *,
        profile: UserProfile,
        analysis: JobAnalysis,
        matching: MatchingResult,
    ) -> TailoredResume:
        payload = {
            "profile": profile.model_dump(),
            "analysis": analysis.model_dump(),
            "matching": matching.model_dump(),
        }
        return await self.run(payload)
