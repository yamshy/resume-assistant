from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class StubResumeLLM:
    """Deterministic LLM substitute used in tests."""

    required_revisions: int = 0
    draft_prefix: str = ""

    def __post_init__(self) -> None:
        self._remaining_revisions = self.required_revisions
        self.plan_calls = 0
        self.draft_calls = 0

    def plan_resume(self, profile: Dict[str, Any], knowledge_hits: List[Dict[str, Any]]) -> Dict[str, Any]:
        self.plan_calls += 1
        summary = profile.get("summary", "") or "Summary pending"
        skills = list(profile.get("skills", []))
        experience = list(profile.get("experience", []))
        if knowledge_hits:
            summary += f" Relevant knowledge: {knowledge_hits[0]['content']}"
        return {
            "summary": summary,
            "skills": skills,
            "experience": experience,
        }

    def draft_resume(self, plan: Dict[str, Any], profile: Dict[str, Any], knowledge_hits: List[Dict[str, Any]]) -> str:
        self.draft_calls += 1
        skills_lines = "\n".join(f"- {skill}" for skill in plan.get("skills", [])) or "- Pending"
        experiences_lines = "\n".join(
            f"- **{item.get('role', 'Role')}**, {item.get('company', 'Company')}: {item.get('impact', 'Impact')}"
            for item in plan.get("experience", [])
        ) or "- Experience pending"
        prefix = f"{self.draft_prefix} \n" if self.draft_prefix else ""
        return (
            f"# {profile.get('name', 'Candidate')}\n\n"
            f"## {plan.get('headline', 'Professional')}\n\n"
            f"{prefix}{plan.get('summary', '')}\n\n"
            "## Skills\n"
            f"{skills_lines}\n\n"
            "## Experience\n"
            f"{experiences_lines}"
        )

    def critique_resume(self, resume_text: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        if self._remaining_revisions > 0:
            self._remaining_revisions -= 1
            return {
                "needs_revision": True,
                "issues": ["Stub requested revision"],
            }
        return {"needs_revision": False, "issues": []}

    def compliance_review(self, resume_text: str, policy: Dict[str, Any]) -> Dict[str, Any]:
        blocklist = [term.lower() for term in policy.get("blocklist", [])]
        lower_resume = resume_text.lower()
        violations = [term for term in blocklist if term in lower_resume]
        if violations:
            return {"status": "rejected", "violations": violations}
        return {"status": "approved", "violations": []}
