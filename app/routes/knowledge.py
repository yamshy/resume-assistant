"""Routes for ingesting resumes into the knowledge base."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile

from app.agents import IngestionAgentError, MissingIngestionLLMError
from app.vectorstore import VectorDocument

router = APIRouter()


@router.post("/knowledge", status_code=201)
async def ingest_knowledge(
    request: Request,
    resumes: list[UploadFile] = File(..., description="Resume files to ingest"),
    notes: str = Form(default=""),
) -> dict[str, Any]:
    """Ingest uploaded resumes into the knowledge store and vector index."""

    if not resumes:
        raise HTTPException(status_code=400, detail="At least one resume file is required.")

    payloads: list[tuple[str, str]] = []
    for upload in resumes:
        raw_bytes = await upload.read()
        await upload.close()
        text = raw_bytes.decode("utf-8", errors="ignore").strip()
        if text:
            payloads.append((upload.filename or "resume.txt", text))

    if not payloads:
        raise HTTPException(
            status_code=400,
            detail="Uploaded resumes were empty or unreadable.",
        )

    ingestor = getattr(request.app.state, "resume_ingestor", None)
    if ingestor is None:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key required for resume ingestion",
        )
    knowledge_store = request.app.state.knowledge_store
    vector_store = request.app.state.vector_store

    try:
        parsed_resumes = await ingestor.parse_many(payloads, notes)
    except (MissingIngestionLLMError, IngestionAgentError):
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key required for resume ingestion",
        ) from None
    store_result = knowledge_store.add_resumes(parsed_resumes)

    documents: list[VectorDocument] = []
    for parsed in parsed_resumes:
        for experience in parsed.experiences:
            for achievement in experience.achievements:
                clean = achievement.strip()
                if not clean:
                    continue
                documents.append(
                    VectorDocument(
                        content=clean,
                        metadata={
                            "source": parsed.source,
                            "company": experience.company,
                            "role": experience.role,
                            "type": "achievement",
                        },
                    )
                )
        for skill in parsed.skills:
            documents.append(
                VectorDocument(
                    content=skill,
                    metadata={"source": parsed.source, "type": "skill"},
                )
            )

    if documents:
        vector_store.add_documents(documents)

    summary_text = build_ingestion_summary(
        len(parsed_resumes),
        store_result.get("skills_added", []),
        store_result.get("achievements_indexed", 0),
    )

    return {
        "ingested": len(parsed_resumes),
        "skills_indexed": store_result.get("skills_added", []),
        "achievements_indexed": store_result.get("achievements_indexed", 0),
        "summary": summary_text,
        "profile_snapshot": store_result.get("profile_snapshot", {}),
    }


def build_ingestion_summary(count: int, skills: list[str], achievements: int) -> str:
    """Summarise the ingestion results for API responses."""

    resume_phrase = f"{count} resume{'s' if count != 1 else ''}"
    achievements_phrase = f"{achievements} achievement{'s' if achievements != 1 else ''}"
    if skills:
        preview = ", ".join(skills[:5])
        skills_phrase = f"{len(skills)} new skill{'s' if len(skills) != 1 else ''}"
        if preview:
            skills_phrase += f" ({preview})"
    else:
        skills_phrase = "no new skills"
    return (
        f"Ingested {resume_phrase} and indexed {achievements_phrase} while capturing {skills_phrase}."
    )
