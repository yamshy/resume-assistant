import os
import tempfile
from textwrap import dedent

from fastapi.testclient import TestClient

from app import create_app


def build_client() -> TestClient:
    temp_dir = tempfile.mkdtemp(prefix="resume-assistant-test-")
    os.environ["KNOWLEDGE_STORE_PATH"] = os.path.join(temp_dir, "knowledge.json")
    app = create_app()
    return TestClient(app)


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


def test_frontend_served_at_root():
    client = build_client()
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    body = response.text
    assert "chat-container" in body
    assert "workflow-form" in body
    assert "resume-files" in body
    assert "job-description" in body


def test_chat_endpoint_returns_conversational_reply():
    client = build_client()
    payload = {
        "message": "How should I improve the summary for an SRE role?",
        "history": [
            {"role": "assistant", "content": "Welcome to the resume assistant!"},
        ],
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["reply"].startswith("Thanks for")
    assert len(data["history"]) == len(payload["history"]) + 2
    assert data["history"][-1]["role"] == "assistant"
    assert any(entry["role"] == "user" for entry in data["history"])
