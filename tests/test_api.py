from fastapi.testclient import TestClient

from app import create_app


def build_client() -> TestClient:
    app = create_app()
    return TestClient(app)


def test_generate_endpoint_returns_structured_resume():
    client = build_client()
    payload = {
        "job_posting": "Senior Python Engineer working on cloud automation",
        "profile": {
            "full_name": "Taylor Candidate",
            "email": "taylor@example.com",
            "phone": "+1 555-0100",
            "location": "Remote",
            "skills": ["Python", "AWS", "Terraform"],
            "years_experience": 7,
            "experience": [
                {
                    "company": "Acme",
                    "role": "Engineer",
                    "start_date": "2017-01-01",
                    "achievements": [
                        "Reduced deployment failures by 45% through CI automation",
                    ],
                }
            ],
        },
    }
    response = client.post("/generate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Taylor Candidate"
    assert data["citations"], "Citations should be populated"
    assert data["confidence_scores"]["overall"] >= 0


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


def test_frontend_served_at_root():
    client = build_client()
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "chat-container" in response.text


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
