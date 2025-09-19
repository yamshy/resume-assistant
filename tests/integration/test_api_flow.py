import base64
from uuid import uuid4

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_end_to_end_pipeline(async_client: AsyncClient) -> None:
    user_id = uuid4()
    resume_text = (
        "Experience: Initech - Data Engineer 2019-2022: Built pipelines; Optimized ETL\n"
        "Skills: Python, SQL, Airflow\n"
        "Education: MS Data Science\n"
    )
    payload = {
        "user_id": str(user_id),
        "resumes": [
            {"filename": "resume.txt", "content": base64.b64encode(resume_text.encode()).decode()},
            {"filename": "notes.txt", "content": base64.b64encode(b"Generalist").decode()},
        ],
    }

    ingest_response = await async_client.post("/api/v1/ingest/", json=payload)
    assert ingest_response.status_code == 200
    body = ingest_response.json()
    assert body["profile"]["experiences"]

    generation_payload = {
        "user_id": str(user_id),
        "job_posting": "Looking for a data engineer with Python and SQL expertise to build ETL systems.",
    }
    generate_response = await async_client.post(
        "/api/v1/generate/resume",
        json=generation_payload,
    )
    assert generate_response.status_code == 200
    data = generate_response.json()
    assert data["resume"]["skills"]
    assert "Python" in {skill["name"] for skill in data["resume"]["skills"]}

    pending = await async_client.get(f"/api/v1/verify/pending?user_id={user_id}")
    assert pending.status_code == 200
    review_items = pending.json()
    if review_items:
        decisions = [
            {"item_id": item["id"], "action": "approve"}
            for item in review_items
        ]
        submit = await async_client.post(
            f"/api/v1/verify/submit?user_id={user_id}",
            json=decisions,
        )
        assert submit.status_code == 200
        assert submit.json()["status"] == "reviews_processed"
