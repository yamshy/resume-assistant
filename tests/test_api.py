import os
import tempfile
from textwrap import dedent

from fastapi.testclient import TestClient

from app import create_app
from app.ingestion import ParsedExperience, ParsedResume
from app.routes.generation import router as generation_router
from app.routes.knowledge import router as knowledge_router


class StubResumeIngestor:
    async def parse_many(self, payloads, notes):  # noqa: D401
        resumes: list[ParsedResume] = []
        for index, (source, _text) in enumerate(payloads, start=1):
            resumes.append(
                ParsedResume(
                    source=source,
                    full_name="Taylor Candidate",
                    email="taylor@example.com",
                    phone="+1 555-0100",
                    skills=["Python", "Terraform", f"Skill-{index}"],
                    experiences=[
                        ParsedExperience(
                            company="Acme Corp",
                            role="Senior Platform Engineer",
                            achievements=[
                                "Reduced deployment failures by 45%",
                                "Migrated infrastructure as code to Terraform modules covering 200+ services",
                            ],
                        )
                    ],
                )
            )
        return resumes


def build_client(*, install_stub_ingestor: bool = True) -> TestClient:
    temp_dir = tempfile.mkdtemp(prefix="resume-assistant-test-")
    os.environ["KNOWLEDGE_STORE_PATH"] = os.path.join(temp_dir, "knowledge.json")
    app = create_app()
    if install_stub_ingestor:
        app.state.resume_ingestor = StubResumeIngestor()
    return TestClient(app)


def test_route_modules_expose_expected_paths() -> None:
    generation_paths = {route.path for route in generation_router.routes}
    assert {"/chat", "/generate", "/validate"}.issubset(generation_paths)

    knowledge_paths = {route.path for route in knowledge_router.routes}
    assert "/knowledge" in knowledge_paths


def test_generate_endpoint_returns_structured_resume():
    client = build_client()

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
    ingest_response = client.post("/knowledge", files=files, data={"notes": "Promoted to lead the SRE program"})
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


def test_validate_endpoint_scores_resume():
    client = build_client()
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


def test_knowledge_ingest_endpoint_adds_documents():
    client = build_client()
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


def test_knowledge_ingest_endpoint_requires_openai_key():
    client = build_client(install_stub_ingestor=False)

    resume_body = dedent(
        """
        Alex Example
        alex@example.com | +1 555-0200
        Principal SRE at CloudWorks
        - Drove SOC2 automation and reduced security review cycles by 50%
        """
    ).strip()

    files = [("resumes", ("alex_resume.txt", resume_body, "text/plain"))]
    response = client.post("/knowledge", files=files)

    assert response.status_code == 503
    assert response.json()["detail"] == "OpenAI API key required for resume ingestion"


def test_frontend_served_at_root():
    client = build_client()
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    body = response.text
    assert "chat-transcript" in body
    assert "chat-form" in body
    assert "resume-upload" in body
    assert "upload-resumes" in body
    assert "/generate" in body


def test_chat_endpoint_returns_grounded_response():
    client = build_client()
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


def test_chat_endpoint_requires_messages():
    client = build_client()

    response = client.post("/chat", json={"messages": []})

    assert response.status_code == 422
