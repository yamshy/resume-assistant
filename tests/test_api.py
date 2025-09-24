import os
import tempfile
from contextlib import ExitStack
from textwrap import dedent
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app import create_app
from app.ingestion import ParsedExperience, ParsedResume
from app.routes.generation import router as generation_router
from app.routes.knowledge import router as knowledge_router


class StubIngestionAgent:
    def __init__(self, *, client=None, **_: object) -> None:
        self.client = client

    async def ingest(self, source: str, text: str, notes: str | None = None) -> ParsedResume:
        del notes
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        full_name = lines[0] if lines else None
        email = None
        phone = None
        for line in lines:
            if "@" in line:
                for segment in line.split("|"):
                    candidate = segment.strip()
                    if "@" in candidate and email is None:
                        email = candidate
                    if any(char.isdigit() for char in candidate) and phone is None:
                        phone = candidate
            if email and phone:
                break
        skills: list[str] = []
        for line in lines:
            if line.lower().startswith("skills:"):
                _, _, trailing = line.partition(":")
                skills.extend(
                    token.strip() for token in trailing.split(",") if token.strip()
                )
        achievements = [
            line.lstrip("-*• ").strip()
            for line in lines
            if line.startswith("-") or line.startswith("•")
        ]
        experiences = []
        if achievements:
            experiences.append(
                ParsedExperience(
                    company="Stub Company",
                    role="Stub Role",
                    achievements=[ach for ach in achievements if ach],
                )
            )
        return ParsedResume(
            source=source,
            full_name=full_name,
            email=email,
            phone=phone,
            skills=list(dict.fromkeys(skills)),
            experiences=experiences,
        )


def build_client(*, with_ingestion_stub: bool = True) -> TestClient:
    temp_dir = tempfile.mkdtemp(prefix="resume-assistant-test-")
    os.environ["KNOWLEDGE_STORE_PATH"] = os.path.join(temp_dir, "knowledge.json")
    if with_ingestion_stub:
        with ExitStack() as stack:
            stack.enter_context(
                patch("app.app_factory.ResumeIngestionAgent", StubIngestionAgent)
            )
            stack.enter_context(
                patch("app.agents.ResumeIngestionAgent", StubIngestionAgent)
            )
            stack.enter_context(
                patch("app.agents.ingestion_agent.ResumeIngestionAgent", StubIngestionAgent)
            )
            app = create_app()
    else:
        app = create_app()
    return TestClient(app)


def test_route_modules_expose_expected_paths() -> None:
    generation_paths = {route.path for route in generation_router.routes}
    assert {"/chat", "/generate", "/validate"}.issubset(generation_paths)

    knowledge_paths = {route.path for route in knowledge_router.routes}
    assert "/knowledge" in knowledge_paths


def test_generate_endpoint_returns_structured_resume():
    with patch(
        "app.monitoring.ResumeMonitor.track_generation", new_callable=AsyncMock
    ) as mock_track_generation:
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
        assert mock_track_generation.await_count == 1
        cache_miss_call = mock_track_generation.await_args_list[0]
        cache_miss_flag = cache_miss_call.kwargs.get("cache_hit")
        if cache_miss_flag is None:
            cache_miss_flag = cache_miss_call.args[-1]
        assert cache_miss_flag is False

        cached_response = client.post("/generate", json=payload)
        assert cached_response.status_code == 200
        assert mock_track_generation.await_count == 2
        cache_hit_call = mock_track_generation.await_args_list[1]
        cache_hit_flag = cache_hit_call.kwargs.get("cache_hit")
        if cache_hit_flag is None:
            cache_hit_flag = cache_hit_call.args[-1]
        assert cache_hit_flag is True


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


def test_knowledge_endpoint_requires_openai_key_when_unconfigured():
    os.environ.pop("OPENAI_API_KEY", None)
    client = build_client(with_ingestion_stub=False)

    resume_body = dedent(
        """
        Taylor Candidate
        taylor@example.com | +1 555-0100
        Skills: Python, AWS, Terraform
        """
    ).strip()

    files = [("resumes", ("resume.txt", resume_body, "text/plain"))]
    response = client.post("/knowledge", files=files)

    assert response.status_code == 503
    assert response.json()["detail"] == "OpenAI API key required for resume ingestion"


def test_root_endpoint_returns_api_metadata():
    client = build_client()
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "AI Resume Assistant API",
        "documentation": "/docs",
    }


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
