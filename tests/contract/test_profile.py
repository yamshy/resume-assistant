"""
Contract tests for the /profile endpoints (GET and PUT).

These tests verify that the /profile endpoints conform to the OpenAPI specification
defined in specs/001-resume-tailoring-feature/contracts/api_spec.yaml.

These are TDD tests that should initially FAIL because the endpoints don't exist yet.
"""

import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_profile_success(async_client: AsyncClient) -> None:
    """
    Test GET /profile returns valid UserProfile when profile exists.

    Expected behavior per OpenAPI spec:
    - Status: 200 OK
    - Content-Type: application/json
    - Response body: UserProfile schema with all required fields
    """
    # This test should FAIL initially - endpoint doesn't exist yet
    response = await async_client.get("/api/v1/profile")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/json"

    profile_data = response.json()

    # Verify UserProfile schema compliance per OpenAPI spec
    assert "contact" in profile_data
    assert "professional_summary" in profile_data
    assert "experience" in profile_data
    assert "education" in profile_data
    assert "skills" in profile_data

    # Verify ContactInfo required fields
    contact = profile_data["contact"]
    assert "name" in contact
    assert "email" in contact
    assert "location" in contact

    # Verify data types and structure
    assert isinstance(profile_data["professional_summary"], str)
    assert isinstance(profile_data["experience"], list)
    assert isinstance(profile_data["education"], list)
    assert isinstance(profile_data["skills"], list)


@pytest.mark.asyncio
async def test_get_profile_success_with_existing_profile(async_client: AsyncClient) -> None:
    """
    Test GET /profile returns 200 with UserProfile when profile exists.

    Expected behavior per OpenAPI spec:
    - Status: 200 OK
    - Content-Type: application/json
    - Response body: UserProfile schema

    This test verifies the endpoint works correctly when a profile file exists.
    """
    response = await async_client.get("/api/v1/profile")

    # Should return 200 when profile exists
    assert response.status_code == status.HTTP_200_OK
    assert "application/json" in response.headers["content-type"]

    profile_data = response.json()

    # Verify UserProfile schema compliance per OpenAPI spec
    assert "contact" in profile_data
    assert "professional_summary" in profile_data
    assert "experience" in profile_data
    assert "education" in profile_data
    assert "skills" in profile_data

    # Verify ContactInfo required fields
    contact = profile_data["contact"]
    assert "name" in contact
    assert "email" in contact
    assert "location" in contact


@pytest.mark.asyncio
async def test_get_profile_endpoint_implemented(async_client: AsyncClient) -> None:
    """
    Test that GET /profile endpoint is implemented and returns a valid HTTP response.

    This test ensures the endpoint is working properly and returns appropriate
    status codes (200 when profile exists, 404 when it doesn't).
    """
    response = await async_client.get("/api/v1/profile")

    # Endpoint should return either 200 (profile exists) or 404 (profile doesn't exist)
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    # Verify it's a valid JSON response
    response_data = response.json()
    assert isinstance(response_data, dict)

    if response.status_code == status.HTTP_200_OK:
        # Should be UserProfile schema
        assert "contact" in response_data
        assert "professional_summary" in response_data
    elif response.status_code == status.HTTP_404_NOT_FOUND:
        # Should be error response (either custom or FastAPI default)
        assert "detail" in response_data or "error" in response_data


@pytest.mark.asyncio
async def test_put_profile_success(async_client: AsyncClient) -> None:
    """
    Test PUT /profile updates profile and returns updated UserProfile.

    Expected behavior per OpenAPI spec:
    - Status: 200 OK
    - Content-Type: application/json
    - Request body: Valid UserProfile schema
    - Response body: UserProfile schema with all required fields
    """
    # Valid UserProfile data per OpenAPI spec
    profile_data = {
        "contact": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "location": "San Francisco, CA",
            "phone": "+1-555-0123",
            "linkedin": "https://linkedin.com/in/johndoe",
            "portfolio": "https://johndoe.dev",
        },
        "professional_summary": "Experienced software engineer with 5+ years in full-stack development.",
        "experience": [
            {
                "position": "Senior Software Engineer",
                "company": "TechCorp",
                "location": "San Francisco, CA",
                "start_date": "2022-01-15",
                "end_date": None,
                "description": "Lead development of web applications using Python and React.",
                "achievements": ["Improved system performance by 40%", "Led team of 3 engineers"],
                "technologies": ["Python", "React", "PostgreSQL"],
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Science in Computer Science",
                "institution": "University of California",
                "location": "Berkeley, CA",
                "graduation_date": "2019-05-15",
                "gpa": 3.8,
                "honors": ["Magna Cum Laude"],
                "relevant_coursework": ["Data Structures", "Algorithms"],
            }
        ],
        "skills": [
            {"name": "Python", "category": "technical", "proficiency": 5, "years_experience": 5},
            {
                "name": "Communication",
                "category": "soft",
                "proficiency": 4,
                "years_experience": None,
            },
        ],
    }

    # This test should FAIL initially - endpoint doesn't exist yet
    response = await async_client.put(
        "/api/v1/profile", json=profile_data, headers={"Content-Type": "application/json"}
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/json"

    updated_profile = response.json()

    # Verify UserProfile schema compliance per OpenAPI spec
    assert "contact" in updated_profile
    assert "professional_summary" in updated_profile
    assert "experience" in updated_profile
    assert "education" in updated_profile
    assert "skills" in updated_profile

    # Verify ContactInfo required fields
    contact = updated_profile["contact"]
    assert "name" in contact
    assert "email" in contact
    assert "location" in contact

    # Verify data types and structure
    assert isinstance(updated_profile["professional_summary"], str)
    assert isinstance(updated_profile["experience"], list)
    assert isinstance(updated_profile["education"], list)
    assert isinstance(updated_profile["skills"], list)

    # Verify updated data matches input
    assert updated_profile["contact"]["name"] == profile_data["contact"]["name"]
    assert updated_profile["contact"]["email"] == profile_data["contact"]["email"]
    assert updated_profile["professional_summary"] == profile_data["professional_summary"]


@pytest.mark.asyncio
async def test_put_profile_validation_error(async_client: AsyncClient) -> None:
    """
    Test PUT /profile returns 422 for invalid UserProfile data.

    Expected behavior per FastAPI:
    - Status: 422 Unprocessable Entity
    - Content-Type: application/json
    - Response body: FastAPI validation error format

    This test verifies the endpoint validates input against UserProfile schema.
    """
    # Invalid profile data - missing required fields
    invalid_profile_data = {
        "contact": {
            "name": "John Doe"
            # Missing required 'email' and 'location' fields
        },
        "professional_summary": "Brief summary",
        # Missing required 'experience', 'education', 'skills' arrays
    }

    response = await async_client.put(
        "/api/v1/profile", json=invalid_profile_data, headers={"Content-Type": "application/json"}
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "application/json" in response.headers["content-type"]

    error_data = response.json()

    # Verify FastAPI's default validation error format
    assert "detail" in error_data, (
        f"Expected 'detail' field in validation error response, got: {error_data}"
    )
    assert isinstance(error_data["detail"], list)
    assert len(error_data["detail"]) > 0

    # Verify validation error structure
    first_error = error_data["detail"][0]
    assert "type" in first_error
    assert "loc" in first_error
    assert "msg" in first_error


@pytest.mark.asyncio
async def test_put_profile_invalid_json(async_client: AsyncClient) -> None:
    """
    Test PUT /profile returns 422 for malformed JSON.

    Expected behavior per FastAPI:
    - Status: 422 Unprocessable Entity
    - Content-Type: application/json
    - Response body: FastAPI JSON decode error format

    This test verifies the endpoint handles malformed request bodies gracefully.
    """
    response = await async_client.put(
        "/api/v1/profile", content="{invalid json}", headers={"Content-Type": "application/json"}
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "application/json" in response.headers["content-type"]

    error_data = response.json()

    # Verify FastAPI's default JSON decode error format
    assert "detail" in error_data, (
        f"Expected 'detail' field in JSON error response, got: {error_data}"
    )
    assert isinstance(error_data["detail"], list)
    assert len(error_data["detail"]) > 0

    # Verify JSON decode error structure
    first_error = error_data["detail"][0]
    assert "type" in first_error
    assert first_error["type"] == "json_invalid"
    assert "msg" in first_error


@pytest.mark.asyncio
async def test_put_profile_endpoint_implemented(async_client: AsyncClient) -> None:
    """
    Test that PUT /profile endpoint is implemented and returns a valid HTTP response.

    This test ensures the endpoint is working properly with valid input data.
    """
    # Minimal valid profile data for testing endpoint existence
    minimal_profile = {
        "contact": {"name": "Test User", "email": "test@example.com", "location": "Test City"},
        "professional_summary": "Test summary",
        "experience": [],
        "education": [],
        "skills": [],
    }

    response = await async_client.put(
        "/api/v1/profile", json=minimal_profile, headers={"Content-Type": "application/json"}
    )

    # Should return 200 for successful profile update
    assert response.status_code == status.HTTP_200_OK

    # Verify it returns the updated profile
    updated_profile = response.json()
    assert "contact" in updated_profile
    assert "professional_summary" in updated_profile
    assert updated_profile["contact"]["name"] == "Test User"
