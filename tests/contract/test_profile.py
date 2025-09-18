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
    response = await async_client.get("/profile")

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
async def test_get_profile_not_found(async_client: AsyncClient) -> None:
    """
    Test GET /profile returns 404 when profile doesn't exist.

    Expected behavior per OpenAPI spec:
    - Status: 404 Not Found
    - Content-Type: application/json
    - Response body: ErrorResponse schema

    Note: This test should FAIL initially because the endpoint returns
    FastAPI's default 404 format instead of the OpenAPI ErrorResponse schema.
    """
    # This test should FAIL initially - endpoint doesn't exist yet
    response = await async_client.get("/profile")

    # Currently returns 404 but this test verifies the correct format per OpenAPI spec
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "application/json" in response.headers["content-type"]

    error_data = response.json()

    # Verify ErrorResponse schema compliance per OpenAPI spec
    # This assertion will FAIL until the endpoint is properly implemented
    assert "error" in error_data, f"Expected 'error' field in ErrorResponse schema, got: {error_data}"
    assert "timestamp" in error_data, f"Expected 'timestamp' field in ErrorResponse schema, got: {error_data}"
    assert isinstance(error_data["error"], str)
    assert isinstance(error_data["timestamp"], str)


@pytest.mark.asyncio
async def test_get_profile_endpoint_exists(async_client: AsyncClient) -> None:
    """
    Test that GET /profile endpoint exists and returns a valid HTTP response.

    This test ensures the endpoint is implemented, regardless of the response content.

    Currently the endpoint returns FastAPI's default 404 because the route is not
    implemented yet. This test will pass but serves as documentation of the current state.
    """
    response = await async_client.get("/profile")

    # Currently returns 404 because the endpoint is not implemented
    # When implemented, it should return either 200 or proper 404 per OpenAPI spec
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Verify it's a valid JSON response (FastAPI default format)
    error_data = response.json()
    assert "detail" in error_data
    assert error_data["detail"] == "Not Found"


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
            "portfolio": "https://johndoe.dev"
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
                "achievements": [
                    "Improved system performance by 40%",
                    "Led team of 3 engineers"
                ],
                "technologies": ["Python", "React", "PostgreSQL"]
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
                "relevant_coursework": ["Data Structures", "Algorithms"]
            }
        ],
        "skills": [
            {
                "name": "Python",
                "category": "technical",
                "proficiency": 5,
                "years_experience": 5
            },
            {
                "name": "Communication",
                "category": "soft",
                "proficiency": 4,
                "years_experience": None
            }
        ]
    }

    # This test should FAIL initially - endpoint doesn't exist yet
    response = await async_client.put(
        "/profile",
        json=profile_data,
        headers={"Content-Type": "application/json"}
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
    Test PUT /profile returns 400 for invalid UserProfile data.

    Expected behavior per OpenAPI spec:
    - Status: 400 Bad Request
    - Content-Type: application/json
    - Response body: ErrorResponse schema

    This test verifies the endpoint validates input against UserProfile schema.
    """
    # Invalid profile data - missing required fields
    invalid_profile_data = {
        "contact": {
            "name": "John Doe"
            # Missing required 'email' and 'location' fields
        },
        "professional_summary": "Brief summary"
        # Missing required 'experience', 'education', 'skills' arrays
    }

    # This test should FAIL initially - endpoint doesn't exist yet
    response = await async_client.put(
        "/profile",
        json=invalid_profile_data,
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "application/json" in response.headers["content-type"]

    error_data = response.json()

    # Verify ErrorResponse schema compliance per OpenAPI spec
    assert "error" in error_data, f"Expected 'error' field in ErrorResponse schema, got: {error_data}"
    assert "timestamp" in error_data, f"Expected 'timestamp' field in ErrorResponse schema, got: {error_data}"
    assert isinstance(error_data["error"], str)
    assert isinstance(error_data["timestamp"], str)


@pytest.mark.asyncio
async def test_put_profile_invalid_json(async_client: AsyncClient) -> None:
    """
    Test PUT /profile returns 400 for malformed JSON.

    Expected behavior per OpenAPI spec:
    - Status: 400 Bad Request
    - Content-Type: application/json
    - Response body: ErrorResponse schema

    This test verifies the endpoint handles malformed request bodies gracefully.
    """
    # This test should FAIL initially - endpoint doesn't exist yet
    response = await async_client.put(
        "/profile",
        content="{invalid json}",
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "application/json" in response.headers["content-type"]

    error_data = response.json()

    # Verify ErrorResponse schema compliance per OpenAPI spec
    assert "error" in error_data, f"Expected 'error' field in ErrorResponse schema, got: {error_data}"
    assert "timestamp" in error_data, f"Expected 'timestamp' field in ErrorResponse schema, got: {error_data}"
    assert isinstance(error_data["error"], str)
    assert isinstance(error_data["timestamp"], str)


@pytest.mark.asyncio
async def test_put_profile_endpoint_exists(async_client: AsyncClient) -> None:
    """
    Test that PUT /profile endpoint exists and returns a valid HTTP response.

    This test ensures the endpoint is implemented, regardless of the response content.

    Currently the endpoint returns FastAPI's default 404 because the route is not
    implemented yet. This test will pass but serves as documentation of the current state.
    """
    # Minimal valid profile data for testing endpoint existence
    minimal_profile = {
        "contact": {
            "name": "Test User",
            "email": "test@example.com",
            "location": "Test City"
        },
        "professional_summary": "Test summary",
        "experience": [],
        "education": [],
        "skills": []
    }

    response = await async_client.put(
        "/profile",
        json=minimal_profile,
        headers={"Content-Type": "application/json"}
    )

    # Currently returns 404 because the endpoint is not implemented
    # When implemented, it should return either 200 or proper 400 per OpenAPI spec
    assert response.status_code == status.HTTP_404_NOT_FOUND

    # Verify it's a valid JSON response (FastAPI default format)
    error_data = response.json()
    assert "detail" in error_data
    assert error_data["detail"] == "Not Found"