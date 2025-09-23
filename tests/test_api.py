import os
import tempfile
from textwrap import dedent

import pytest
from fastapi.testclient import TestClient

from app import create_app
from app.ingestion import ParsedExperience, ParsedResume


class StubResumeIngestionAgent:
    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        pass

    async def ingest(
        self, source: str, text: str, notes: str | None = None
    ) -> ParsedResume:
        full_name = _extract_full_name(text)
        skills = _extract_skills(text)
        achievements = _extract_achievements(text)
        experiences = [
            ParsedExperience(
                company="CloudWorks",
                role="Principal SRE",
                achievements=achievements or ["Delivered measurable improvements"],
                start_date="2020-01-01",
                end_date=None,
                location="Remote",
            )
        ]
        return ParsedResume(
            source=source,
            full_name=full_name,
            email="candidate@example.com",
            phone="+1 555-0100",
            skills=skills or ["Python"],
            experiences=experiences,
        )


def _extract_full_name(text: str) -> str:
    for line in text.splitlines():
        candidate = line.strip()
        if candidate:
            return candidate
    return "Test Candidate"


def _extract_skills(text: str) -> list[str]:
    for line in text.splitlines():
        if "skills" in line.lower():
            _, _, trailing = line.partition(":")
            tokens = trailing if trailing else line
            return [token.strip() for token in tokens.split(",") if token.strip()]
    return []


def _extract_achievements(text: str) -> list[str]:
    achievements: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("-") or stripped.startswith("•"):
            achievements.append(stripped.lstrip("-• ").strip())
    return achievements


def build_client(
    monkeypatch: pytest.MonkeyPatch, *, stub_ingestion: bool = True
) -> TestClient:
    temp_dir = tempfile.mkdtemp(prefix="resume-assistant-test-")
    monkeypatch.setenv("KNOWLEDGE_STORE_PATH", os.path.join(temp_dir, "knowledge.json"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    if stub_ingestion:
        monkeypatch.setattr("app.app_factory.ResumeIngestionAgent", StubResumeIngestionAgent)
    app = create_app()
    return TestClient(app)


def test_generate_endpoint_returns_structured_resume(monkeypatch):
    client = build_client(monkeypatch)

    resume_body = dedent(
        """
        Taylor Candidate
        taylor@example.com | +1 555-0100
        Skills: Python, AWS, Terraform
        Senior Platform Engineer at Acme Corp
        - Reduced deployment failures by 45% through CI automation
        - Migrated infrastructure as code to Terraform modules covering 200+ services
        """
    ).strip()

    files = [
        (
            "resumes",
            ("taylor_resume.txt", resume_body, "text/plain"),
        )
    ]
    ingest_response = client.post(
        "/knowledge", files=files, data={"notes": "Promoted to lead the SRE program"}
    )
    assert ingest_response.status_code == 201

    payload = {
        "job_posting": "Senior Python Engineer working on cloud automation",
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Taylor Candidate"
    assert data["citations"], "Citations should be populated"
    assert data["confidence_scores"]["overall"] >= 0
    assert "Python" in data.get("skills", [])
    assert data.get("metadata", {}).get("profile_source") == "knowledge-base"


def test_validate_endpoint_scores_resume(monkeypatch):
    client = build_client(monkeypatch)
    resume_text = """
    Taylor Candidate
    taylor@example.com | +1 555-0100

    Summary
    Senior engineer delivering 45% reduction in deployment failures across AWS.

    Experience
    - Reduced deployment failures by 45%
    - Improved delivery speed by 30%
    """
    response = client.post("/validate", json={"resume_text": resume_text})
    assert response.status_code == 200
    data = response.json()
    assert 0 <= data["ats_compatibility"] <= 1
    assert 0 <= data["keyword_density"] <= 1


def test_knowledge_ingest_endpoint_adds_documents(monkeypatch):
    client = build_client(monkeypatch)
    vector_store = client.app.state.vector_store
    existing_docs = len(getattr(vector_store, "_documents", []))

    resume_one = dedent(
        """
        Alex Example
        alex@example.com | +1 555-0200
        Skills: Kubernetes, Terraform, Observability
        Principal SRE at CloudWorks
        - Drove SOC2 automation and reduced security review cycles by 50%
        - Built global observability platform adopted by 45 teams
        """
    ).strip()

    resume_two = dedent(
        """
        Alex Example
        alex@example.com | +1 555-0200
        Skills: Leadership, Hiring, Coaching
        Director of Engineering at LaunchPad
        - Introduced hiring rubric that increased offer acceptance to 75%
        - Scaled platform reliability reviews across five product areas
        """
    ).strip()

    files = [
        ("resumes", ("alex_sre.txt", resume_one, "text/plain")),
        ("resumes", ("alex_leadership.txt", resume_two, "text/plain")),
    ]
    response = client.post(
        "/knowledge",
        files=files,
        data={"notes": "Ensure leadership growth is captured"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["ingested"] == 2
    assert data["skills_indexed"], "Expected newly indexed skills"
    assert data["achievements_indexed"] >= 2
    snapshot = data.get("profile_snapshot", {})
    assert snapshot.get("skills"), "Profile snapshot should include skills"
    assert snapshot.get("experience"), "Profile snapshot should include experience"
    updated_docs = len(getattr(vector_store, "_documents", []))
    expected_minimum = data["achievements_indexed"] + len(data["skills_indexed"])
    assert updated_docs >= existing_docs + expected_minimum


def test_frontend_served_at_root(monkeypatch):
    client = build_client(monkeypatch)
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    body = response.text
    assert "chat-transcript" in body
    assert "chat-form" in body
    assert "resume-upload" in body
    assert "upload-resumes" in body
    assert "/generate" in body


def test_chat_endpoint_returns_grounded_response(monkeypatch):
    client = build_client(monkeypatch)
    payload = {
        "messages": [
            {"role": "user", "content": "How can I talk about achievements?"},
        ]
    }

    response = client.post("/chat", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["reply"]["role"] == "assistant"
    assert "resume playbook" in data["reply"]["content"].lower()
    assert data["reply"].get("metadata", {}).get("grounding")
    assert data["session"]["turns"] == 1


def test_chat_endpoint_requires_messages(monkeypatch):
    client = build_client(monkeypatch)

    response = client.post("/chat", json={"messages": []})

    assert response.status_code == 422


def test_knowledge_endpoint_requires_openai_key(monkeypatch):
    client = build_client(monkeypatch, stub_ingestion=False)

    resume_body = dedent(
        """
        Taylor Candidate
        taylor@example.com | +1 555-0100
        Skills: Python, AWS, Terraform
        """
    ).strip()

    files = [
        (
            "resumes",
            ("taylor_resume.txt", resume_body, "text/plain"),
        )
    ]

    response = client.post("/knowledge", files=files)
    assert response.status_code == 503
    assert response.json()["detail"] == "OpenAI API key required for resume ingestion"
