from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.core.settings import Settings, get_settings
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def temp_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    base = tmp_path / "data"
    base.mkdir()
    (base / "resumes").mkdir()
    monkeypatch.setenv("PROFILE_STORAGE_PATH", str(base / "profile.json"))
    monkeypatch.setenv("RESUME_STORAGE_DIR", str(base / "resumes"))
    return base


@pytest.fixture(autouse=True)
def settings_override(temp_data_dir: Path) -> None:
    settings = Settings()
    settings.STORAGE_BASE_DIR = temp_data_dir
    settings.PROFILE_STORAGE_PATH = temp_data_dir / "profile.json"
    settings.RESUME_STORAGE_DIR = temp_data_dir / "resumes"

    app.dependency_overrides[get_settings] = lambda: settings
    yield
    app.dependency_overrides.pop(get_settings, None)


@pytest.fixture
def sample_profile_payload() -> dict[str, object]:
    return {
        "version": "1.0",
        "metadata": {
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
        },
        "contact": {
            "name": "John Developer",
            "email": "john@example.com",
            "location": "San Francisco, CA",
            "linkedin": "https://linkedin.com/in/johndeveloper",
        },
        "professional_summary": (
            "Experienced software engineer with 6 years developing scalable backend systems. "
            "Expertise in Python, cloud infrastructure, and building high-performance APIs."
        ),
        "experience": [
            {
                "position": "Senior Software Engineer",
                "company": "StartupXYZ",
                "location": "San Francisco, CA",
                "start_date": "2019-01-15",
                "end_date": None,
                "description": "Lead backend development for core platform serving 100k+ users.",
                "achievements": [
                    "Reduced API response time by 40% through optimization and caching",
                    "Designed and implemented microservices architecture supporting 10x growth",
                    "Mentored 3 junior developers and led technical architecture discussions",
                ],
                "technologies": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"],
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Science in Computer Science",
                "institution": "UC Berkeley",
                "location": "Berkeley, CA",
                "graduation_date": "2018-05-15",
                "honors": ["Magna Cum Laude", "Dean's List"],
                "relevant_coursework": ["Distributed Systems", "Algorithms"],
            }
        ],
        "skills": [
            {"name": "Python", "category": "technical", "proficiency": 5, "years_experience": 6},
            {"name": "FastAPI", "category": "technical", "proficiency": 4, "years_experience": 3},
            {"name": "PostgreSQL", "category": "technical", "proficiency": 4, "years_experience": 4},
            {"name": "AWS", "category": "technical", "proficiency": 3, "years_experience": 2},
            {"name": "Docker", "category": "technical", "proficiency": 4, "years_experience": 3},
        ],
        "projects": [],
        "publications": [],
        "awards": [],
        "volunteer": [],
        "languages": [],
    }


@pytest.fixture
def sample_job_posting() -> str:
    return (
        "Senior Software Engineer - Backend Development\n"
        "TechCorp Inc.\n\n"
        "We are looking for a Senior Software Engineer to join our backend development team.\n"
        "The ideal candidate will have 5+ years of experience building scalable web applications\n"
        "using Python, FastAPI, and cloud technologies.\n\n"
        "Requirements:\n"
        "- Bachelor's degree in Computer Science or related field\n"
        "- 5+ years of Python development experience\n"
        "- Experience with FastAPI, Django, or Flask frameworks\n"
        "- Strong knowledge of PostgreSQL and database design\n"
        "- Experience with AWS, Docker, and Kubernetes\n"
        "- Understanding of microservices architecture\n"
        "- Excellent problem-solving skills and teamwork abilities\n\n"
        "Preferred Qualifications:\n"
        "- Experience with machine learning or AI systems\n"
        "- Previous work in fast-paced startup environments\n"
        "- Contributions to open source projects\n\n"
        "We offer competitive salary, excellent health benefits, flexible work arrangements,\n"
        "and opportunities for professional growth in a collaborative environment."
    )


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture
def mock_agent():
    with patch("resume_core.agents.base_agent.Agent.run") as mock_run:
        mock_run.return_value = {
            "analysis": "Mocked analysis result",
            "confidence": 0.95,
        }
        yield mock_run


@pytest.fixture
def mock_agent_async():
    async def mock_run(self, text: str):
        return {
            "analysis": f"Analyzed: {text}",
            "confidence": 0.90,
        }

    with patch("resume_core.agents.base_agent.Agent.run", new=mock_run):
        yield
