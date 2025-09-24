from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List


@dataclass(slots=True)
class ResumeRendererTool:
    """Render a structured resume payload into a deterministic markdown template."""

    name: str = "resume_renderer"
    description: str = "Format resume profiles into markdown for downstream delivery."

    def render(self, profile: Dict[str, object]) -> str:
        headline = profile.get("headline") or "Professional Summary"
        summary = profile.get("summary") or "No summary provided."
        skills = self._format_bullets(profile.get("skills", []))
        experiences = self._format_experience(profile.get("experience", []))
        sections: List[str] = [f"# {profile.get('name', 'Candidate')}\n", f"## {headline}\n", summary.strip(), "\n", "## Skills", skills, "\n", "## Experience", experiences]
        return "\n".join(section for section in sections if section)

    @staticmethod
    def _format_bullets(skills: Iterable[str]) -> str:
        rows = [f"- {skill}" for skill in skills]
        return "\n".join(rows) if rows else "- Skills pending collection"

    @staticmethod
    def _format_experience(experiences: Iterable[Dict[str, str]]) -> str:
        blocks: List[str] = []
        for exp in experiences:
            role = exp.get("role", "Role Unknown")
            company = exp.get("company", "Company Unknown")
            impact = exp.get("impact", "Impact pending")
            blocks.append(f"- **{role}**, {company}: {impact}")
        return "\n".join(blocks) if blocks else "- Experience pending collection"


__all__ = ["ResumeRendererTool"]
