from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from resume_core.agents.job_analysis_agent import JobAnalysisAgent

router = APIRouter(tags=["jobs"])
_job_agent = JobAnalysisAgent()


class JobAnalysisRequest(BaseModel):
    job_posting: str


@router.post("/jobs/analyze")
async def analyze_job(request: JobAnalysisRequest) -> dict[str, dict]:
    analysis = await _job_agent.analyze(job_posting=request.job_posting)
    return {"analysis": analysis.model_dump()}
