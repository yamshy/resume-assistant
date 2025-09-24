"""Live integration tests that exercise the OpenAI-backed LLM."""

from __future__ import annotations

import os
from typing import Dict, List

import pytest

from app.tools.llm import OpenAIResumeLLM

pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY must be set to run live OpenAI tests",
)


def _assert_non_empty_str(value: str) -> None:
    assert isinstance(value, str)
    assert value.strip(), "expected non-empty string"


def test_openai_resume_llm_end_to_end_live() -> None:
    """Ensure the OpenAI LLM can plan, draft, critique, and review a resume."""

    llm = OpenAIResumeLLM(model="gpt-4o-mini", temperature=0)

    profile: Dict[str, object] = {
        "name": "Jordan Rivera",
        "headline": "Full-stack engineer transitioning into ML ops",
        "skills": ["python", "docker", "ml ops"],
        "experience": [
            {
                "role": "Software Engineer",
                "company": "Acme Corp",
                "highlights": ["Built CI/CD pipelines", "Led migration to containers"],
            }
        ],
    }
    knowledge_hits: List[Dict[str, object]] = [
        {
            "title": "Recent achievements",
            "content": "Implemented observability tooling and automated deployment scripts.",
        }
    ]

    plan = llm.plan_resume(profile, knowledge_hits)
    _assert_non_empty_str(plan["summary"])
    assert plan["skills"], "expected at least one skill"
    assert all(isinstance(skill, str) and skill for skill in plan["skills"])
    assert plan["experience"], "expected experience entries"
    assert all(isinstance(item, dict) for item in plan["experience"])

    resume_markdown = llm.draft_resume(plan, profile, knowledge_hits)
    _assert_non_empty_str(resume_markdown)
    assert "Summary" in resume_markdown
    assert "Skills" in resume_markdown
    assert "Experience" in resume_markdown

    critique = llm.critique_resume(resume_markdown, profile)
    assert set(critique.keys()) == {"needs_revision", "issues"}
    assert isinstance(critique["needs_revision"], bool)
    assert isinstance(critique["issues"], list)

    policy = {
        "rules": [
            "Reject resumes containing disallowed phrases like 'forbidden'.",
            "Approve resumes that present professional experience without sensitive data.",
        ]
    }
    compliance = llm.compliance_review(resume_markdown, policy)
    assert compliance["status"] in {"approved", "rejected"}
    assert isinstance(compliance["violations"], list)

