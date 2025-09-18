import pytest
from httpx import AsyncClient

SAMPLE_PROFILE = {
    "contact": {
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "phone": "+44 1234 567890",
        "location": "London, UK",
    },
    "summary": "Innovative engineer with focus on analytics.",
    "experience": [
        {
            "role": "Data Scientist",
            "company": "Analytica",
            "start_date": "2020-01",
            "end_date": "2023-06",
            "achievements": [
                {
                    "description": "Built ML pipeline",
                    "metrics": "Improved conversion by 20%",
                }
            ],
            "skills": ["python", "machine learning", "data visualization"],
        }
    ],
    "education": [
        {
            "degree": "MSc Computer Science",
            "institution": "University of Oxford",
            "start_date": "2018-09",
            "end_date": "2019-06",
            "honors": "Distinction",
        }
    ],
    "skills": [
        {"name": "Python", "level": "expert"},
        {"name": "Machine Learning", "level": "advanced"},
    ],
    "projects": [
        {
            "name": "Resume AI",
            "description": "Built resume tailoring assistant",
            "skills": ["python", "fastapi"],
        }
    ],
    "certifications": [
        {
            "name": "AWS Solutions Architect",
            "authority": "Amazon Web Services",
            "year": 2022,
        }
    ],
    "languages": [
        {"name": "English", "proficiency": "native"},
        {"name": "French", "proficiency": "intermediate"},
    ],
}


@pytest.mark.asyncio
async def test_get_profile_returns_default(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/profile")
    assert response.status_code == 200
    payload = response.json()
    assert payload["profile"]["contact"]["name"] == ""
    assert payload["profile"]["experience"] == []
    assert payload["profile"]["skills"] == []


@pytest.mark.asyncio
async def test_put_profile_persists_changes(async_client: AsyncClient) -> None:
    response = await async_client.put("/api/v1/profile", json=SAMPLE_PROFILE)
    assert response.status_code == 200
    saved = response.json()["profile"]
    assert saved["contact"]["name"] == SAMPLE_PROFILE["contact"]["name"]
    assert len(saved["experience"]) == 1

    response_get = await async_client.get("/api/v1/profile")
    assert response_get.status_code == 200
    profile = response_get.json()["profile"]
    assert profile["contact"]["email"] == SAMPLE_PROFILE["contact"]["email"]
    assert profile["skills"][0]["name"].lower() == "python"
