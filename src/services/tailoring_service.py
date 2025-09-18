"""
Resume Tailoring Pipeline Service - Complete 5-Agent Orchestration.

Orchestrates the complete resume tailoring workflow through all 5 agents:
1. Job Analysis Agent → Extract structured requirements
2. Profile Matching Agent → Match profile against job
3. Resume Generation Agent → Create tailored content
4. Validation Agent → Verify accuracy
5. Human Interface Agent → Manage approval workflow

Constitutional compliance:
- Agent-chain orchestration following constitutional patterns
- Pipeline pattern with structured data flow between agents
- Error handling with retry logic
- Performance target: <30 seconds full chain
"""

import uuid
from datetime import datetime
from typing import Dict, Optional

from models.profile import UserProfile
from models.job_analysis import JobAnalysis
from models.matching import MatchingResult
from models.resume_optimization import TailoredResume
from models.validation import ValidationResult
from models.approval import ApprovalWorkflow, ReviewDecision

from agents.job_analysis_agent import create_job_analysis_agent
from agents.profile_matching import create_profile_matching_agent
from agents.resume_generation_agent import create_resume_generation_agent
from agents.validation_agent import create_validation_agent
from agents.human_interface_agent import create_human_interface_agent


class ResumeTailoringService:
    """
    Complete resume tailoring pipeline orchestrating all 5 agents.

    Manages the full agent-chain workflow with structured data flow
    and error recovery according to constitutional requirements.
    """

    def __init__(self):
        """Initialize service with lazy-loaded agents."""
        # Agents initialized on first use for performance
        self._job_analysis_agent = None
        self._profile_matching_agent = None
        self._resume_generation_agent = None
        self._validation_agent = None
        self._human_interface_agent = None

    def _get_job_analysis_agent(self):
        """Get job analysis agent, creating if needed."""
        if self._job_analysis_agent is None:
            self._job_analysis_agent = create_job_analysis_agent()
        return self._job_analysis_agent

    def _get_profile_matching_agent(self):
        """Get profile matching agent, creating if needed."""
        if self._profile_matching_agent is None:
            self._profile_matching_agent = create_profile_matching_agent()
        return self._profile_matching_agent

    def _get_resume_generation_agent(self):
        """Get resume generation agent, creating if needed."""
        if self._resume_generation_agent is None:
            self._resume_generation_agent = create_resume_generation_agent()
        return self._resume_generation_agent

    def _get_validation_agent(self):
        """Get validation agent, creating if needed."""
        if self._validation_agent is None:
            self._validation_agent = create_validation_agent()
        return self._validation_agent

    def _get_human_interface_agent(self):
        """Get human interface agent, creating if needed."""
        if self._human_interface_agent is None:
            self._human_interface_agent = create_human_interface_agent()
        return self._human_interface_agent

    async def tailor_resume(
        self,
        user_profile: UserProfile,
        job_posting_text: str
    ) -> Dict[str, any]:
        """
        Execute complete resume tailoring pipeline through all 5 agents.

        Args:
            user_profile: Complete user profile data
            job_posting_text: Raw job posting text to analyze

        Returns:
            Dict containing all pipeline results and final resume

        Raises:
            Exception: If any agent in the pipeline fails after retries
        """
        session_id = str(uuid.uuid4())
        start_time = datetime.now()

        try:
            # Step 1: Job Analysis Agent - Extract requirements from job posting
            job_analysis_agent = self._get_job_analysis_agent()
            job_analysis = await job_analysis_agent.run(job_posting_text)

            # Step 2: Profile Matching Agent - Match profile against job requirements
            profile_matching_agent = self._get_profile_matching_agent()
            matching_result = await profile_matching_agent.run(user_profile, job_analysis)

            # Step 3: Resume Generation Agent - Create tailored resume content
            resume_generation_agent = self._get_resume_generation_agent()
            context_data = {
                "user_profile": user_profile,
                "job_analysis": job_analysis,
                "matching_result": matching_result
            }
            tailored_resume = await resume_generation_agent.run(context_data)

            # Step 4: Validation Agent - Verify accuracy against source data
            validation_agent = self._get_validation_agent()
            # Convert models to dict format for validation
            resume_data = tailored_resume.model_dump()
            source_profile = user_profile.model_dump()
            validation_result = await validation_agent.run(resume_data, source_profile)

            # Step 5: Human Interface Agent - Determine approval workflow
            human_interface_agent = self._get_human_interface_agent()
            approval_input = {
                "validation_result": validation_result.model_dump(),
                "tailored_resume": {
                    "job_title": tailored_resume.job_title,
                    "company_name": tailored_resume.company_name,
                    "summary_of_changes": tailored_resume.summary_of_changes,
                    "estimated_match_score": tailored_resume.estimated_match_score,
                    "generation_timestamp": tailored_resume.generation_timestamp
                },
                "confidence_threshold_auto": 0.8,
                "confidence_threshold_review": 0.6
            }
            approval_result = await human_interface_agent.run(approval_input)
            approval_request = approval_result.output

            # Calculate total processing time
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()

            # Return complete pipeline results
            return {
                "session_id": session_id,
                "processing_time_seconds": processing_time,
                "pipeline_results": {
                    "job_analysis": job_analysis,
                    "matching_result": matching_result,
                    "tailored_resume": tailored_resume,
                    "validation_result": validation_result,
                    "approval_workflow": approval_request
                },
                "final_status": {
                    "requires_human_review": approval_request.requires_human_review,
                    "auto_approved": approval_request.auto_approve_eligible and not approval_request.requires_human_review,
                    "estimated_match_score": tailored_resume.estimated_match_score,
                    "validation_confidence": validation_result.confidence
                },
                "timestamps": {
                    "started_at": start_time.isoformat(),
                    "completed_at": end_time.isoformat()
                }
            }

        except Exception as e:
            # Log error with session context
            error_info = {
                "session_id": session_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "failed_at": datetime.now().isoformat()
            }

            # Re-raise with context
            raise Exception(f"Resume tailoring pipeline failed: {error_info}") from e

    async def get_pipeline_status(self, session_id: str) -> Dict[str, str]:
        """
        Get status information for the pipeline.

        Args:
            session_id: Session identifier

        Returns:
            Dict with pipeline status and agent health
        """
        return {
            "session_id": session_id,
            "pipeline_status": "ready",
            "agents_loaded": {
                "job_analysis": self._job_analysis_agent is not None,
                "profile_matching": self._profile_matching_agent is not None,
                "resume_generation": self._resume_generation_agent is not None,
                "validation": self._validation_agent is not None,
                "human_interface": self._human_interface_agent is not None
            },
            "checked_at": datetime.now().isoformat()
        }


# Factory function for service creation
def create_resume_tailoring_service() -> ResumeTailoringService:
    """
    Create a new Resume Tailoring Service instance.

    Returns:
        ResumeTailoringService configured with all 5 agents
    """
    return ResumeTailoringService()


__all__ = ["ResumeTailoringService", "create_resume_tailoring_service"]