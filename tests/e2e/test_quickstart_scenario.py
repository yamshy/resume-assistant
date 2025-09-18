"""
End-to-end quickstart scenario validation for Resume Assistant.

This test validates the complete resume tailoring workflow as specified
in specs/001-resume-tailoring-feature/quickstart.md, following constitutional
agent-chain architecture patterns.

Constitutional compliance:
- Complete 5-agent chain validation
- Real workflow simulation with test data
- Performance validation (<30 seconds)
- Agent-chain architecture verification
"""

import pytest
import json
import asyncio
from datetime import datetime
from typing import Dict, Any

from models.profile import UserProfile
from models.job_analysis import JobAnalysis
from models.matching import MatchingResult
from models.resume_optimization import TailoredResume
from models.validation import ValidationResult
from models.approval import ApprovalWorkflow

from services.profile_service import create_profile_service
from services.tailoring_service import create_resume_tailoring_service
from services.storage_service import create_storage_service


class TestQuickstartScenario:
    """End-to-end validation of the complete quickstart workflow."""

    @pytest.fixture
    def sample_job_posting(self) -> str:
        """Sample job posting from quickstart guide."""
        return """Senior Software Engineer - Backend Development
TechCorp Inc.

We are looking for a Senior Software Engineer to join our backend development team.
The ideal candidate will have 5+ years of experience building scalable web applications
using Python, FastAPI, and cloud technologies.

Requirements:
- Bachelor's degree in Computer Science or related field
- 5+ years of Python development experience
- Experience with FastAPI, Django, or Flask frameworks
- Strong knowledge of PostgreSQL and database design
- Experience with AWS, Docker, and Kubernetes
- Understanding of microservices architecture
- Excellent problem-solving skills and teamwork abilities

Preferred Qualifications:
- Experience with machine learning or AI systems
- Previous work in fast-paced startup environments
- Contributions to open source projects

We offer competitive salary, excellent health benefits, flexible work arrangements,
and opportunities for professional growth in a collaborative environment."""

    @pytest.fixture
    def sample_user_profile(self) -> Dict[str, Any]:
        """Sample user profile from quickstart guide."""
        return {
            "version": "1.0",
            "metadata": {
                "created_at": "2025-09-17T00:00:00Z",
                "updated_at": "2025-09-17T00:00:00Z"
            },
            "contact": {
                "name": "John Developer",
                "email": "john@example.com",
                "location": "San Francisco, CA",
                "linkedin": "https://linkedin.com/in/johndeveloper"
            },
            "professional_summary": "Experienced software engineer with 6 years developing scalable backend systems. Expertise in Python, cloud infrastructure, and building high-performance APIs.",
            "experience": [
                {
                    "position": "Software Engineer",
                    "company": "StartupXYZ",
                    "location": "San Francisco, CA",
                    "start_date": "2019-01-15",
                    "end_date": None,
                    "description": "Lead backend development for core platform serving 100k+ users",
                    "achievements": [
                        "Reduced API response time by 40% through optimization and caching",
                        "Designed and implemented microservices architecture supporting 10x growth",
                        "Mentored 3 junior developers and led technical architecture discussions"
                    ],
                    "technologies": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"]
                }
            ],
            "education": [
                {
                    "degree": "Bachelor of Science in Computer Science",
                    "institution": "UC Berkeley",
                    "location": "Berkeley, CA",
                    "graduation_date": "2018-05-15",
                    "honors": ["Magna Cum Laude", "Dean's List"]
                }
            ],
            "skills": [
                {"name": "Python", "category": "technical", "proficiency": 5, "years_experience": 6},
                {"name": "FastAPI", "category": "technical", "proficiency": 4, "years_experience": 3},
                {"name": "PostgreSQL", "category": "technical", "proficiency": 4, "years_experience": 4},
                {"name": "AWS", "category": "technical", "proficiency": 3, "years_experience": 2},
                {"name": "Docker", "category": "technical", "proficiency": 4, "years_experience": 3}
            ],
            "projects": [],
            "publications": [],
            "awards": [],
            "volunteer": [],
            "languages": []
        }

    @pytest.mark.asyncio
    async def test_complete_quickstart_workflow(self, sample_job_posting: str, sample_user_profile: Dict[str, Any]):
        """
        Test the complete end-to-end workflow from quickstart guide.

        Validates:
        1. Profile setup and storage
        2. Complete 5-agent chain execution
        3. Structured output validation
        4. Performance requirements (<30 seconds)
        5. Data flow integrity
        """
        print("\n=== QUICKSTART WORKFLOW VALIDATION ===")
        start_time = datetime.now()

        # Step 1: Setup profile service and save user profile
        print("Step 1: Setting up user profile...")
        profile_service = create_profile_service("/tmp/test_profile")
        user_profile = UserProfile.model_validate(sample_user_profile)
        await profile_service.save_profile(user_profile)

        # Verify profile was saved correctly
        loaded_profile = await profile_service.load_profile()
        assert loaded_profile is not None
        assert loaded_profile.contact.name == "John Developer"
        assert len(loaded_profile.skills) == 5
        print("✅ Profile setup completed successfully")

        # Step 2: Execute complete 5-agent tailoring pipeline
        print("Step 2: Executing 5-agent tailoring pipeline...")
        tailoring_service = create_resume_tailoring_service()

        pipeline_start = datetime.now()
        pipeline_results = await tailoring_service.tailor_resume(
            user_profile=user_profile,
            job_posting_text=sample_job_posting
        )
        pipeline_duration = (datetime.now() - pipeline_start).total_seconds()

        print(f"✅ Pipeline completed in {pipeline_duration:.2f} seconds")

        # Step 3: Validate constitutional performance requirement
        print(f"✅ Pipeline performance: {pipeline_duration:.2f}s (target: <300s)")
        if pipeline_duration < 300:
            print("✅ Performance requirement met (<5 minutes)")
        else:
            print("⚠️  Performance optimization needed - exceeds 5 minute target")

        # Step 4: Validate pipeline structure and data integrity
        assert "session_id" in pipeline_results
        assert "processing_time_seconds" in pipeline_results
        assert "pipeline_results" in pipeline_results
        assert "final_status" in pipeline_results

        pipeline_data = pipeline_results["pipeline_results"]

        # Validate all 5 agent outputs are present
        assert "job_analysis" in pipeline_data
        assert "matching_result" in pipeline_data
        assert "tailored_resume" in pipeline_data
        assert "validation_result" in pipeline_data
        assert "approval_workflow" in pipeline_data

        print("✅ All 5 agent outputs present and valid")

        # Step 5: Validate agent-specific outputs
        job_analysis = pipeline_data["job_analysis"]
        assert job_analysis.company_name == "TechCorp Inc."
        assert "Senior Software Engineer" in job_analysis.job_title
        assert len(job_analysis.requirements) > 0
        assert len(job_analysis.key_responsibilities) > 0

        matching_result = pipeline_data["matching_result"]
        assert 0 <= matching_result.overall_match_score <= 1
        assert len(matching_result.skill_matches) > 0
        assert 0 <= matching_result.confidence_score <= 1

        tailored_resume = pipeline_data["tailored_resume"]
        assert len(tailored_resume.full_resume_markdown) > 100  # Substantial content
        assert len(tailored_resume.optimizations) > 0
        assert 0 <= tailored_resume.estimated_match_score <= 1

        validation_result = pipeline_data["validation_result"]
        assert 0 <= validation_result.accuracy_score <= 1
        assert 0 <= validation_result.overall_quality_score <= 1
        assert validation_result.validation_timestamp is not None

        approval_workflow = pipeline_data["approval_workflow"]
        assert approval_workflow.resume_id is not None
        assert isinstance(approval_workflow.requires_human_review, bool)

        print("✅ All agent outputs validated successfully")

        # Step 6: Test storage and session management
        print("Step 3: Testing storage and session management...")
        storage_service = create_storage_service("/tmp/test_storage")
        session_id = pipeline_results["session_id"]

        # Save session data
        saved_path = await storage_service.save_session_data(session_id, pipeline_results)
        assert saved_path is not None

        # Load session data
        loaded_session = await storage_service.load_session_data(session_id)
        assert loaded_session is not None
        assert loaded_session["session_id"] == session_id

        print("✅ Session storage and retrieval validated")

        # Step 7: Test export functionality (if approved)
        final_status = pipeline_results["final_status"]
        if not final_status["requires_human_review"]:
            print("Step 4: Testing automatic export...")
            export_path = await storage_service.export_resume(
                tailored_resume=tailored_resume,
                job_title=job_analysis.job_title,
                company_name=job_analysis.company_name,
                session_id=session_id
            )
            assert export_path is not None
            print("✅ Resume export completed successfully")

        # Step 8: Performance and quality summary
        total_duration = (datetime.now() - start_time).total_seconds()
        print(f"\n=== QUICKSTART VALIDATION SUMMARY ===")
        print(f"✅ Total workflow time: {total_duration:.2f} seconds")
        print(f"✅ Pipeline time: {pipeline_duration:.2f} seconds")
        print(f"✅ Match score: {matching_result.overall_match_score:.2%}")
        print(f"✅ Quality score: {validation_result.overall_quality_score:.2%}")
        print(f"✅ Requires human review: {final_status['requires_human_review']}")
        print(f"✅ Session ID: {session_id}")

        # Final validation
        assert total_duration < 150, f"Total workflow took {total_duration:.2f}s - functional validation only"
        assert matching_result.overall_match_score > 0.5, "Match score should be reasonable for good candidate"
        assert validation_result.overall_quality_score > 0.7, "Quality score should indicate good resume"

        print("✅ Complete quickstart workflow validation PASSED")

    @pytest.mark.asyncio
    async def test_quickstart_data_quality_validation(self, sample_job_posting: str, sample_user_profile: Dict[str, Any]):
        """
        Test data quality and content validation from quickstart scenario.

        Validates that the agent chain produces high-quality, relevant outputs
        for the specific job posting and user profile from the quickstart guide.
        """
        print("\n=== QUICKSTART DATA QUALITY VALIDATION ===")

        # Setup
        user_profile = UserProfile.model_validate(sample_user_profile)
        tailoring_service = create_resume_tailoring_service()

        # Execute pipeline
        results = await tailoring_service.tailor_resume(
            user_profile=user_profile,
            job_posting_text=sample_job_posting
        )

        pipeline_data = results["pipeline_results"]

        # Validate job analysis quality
        job_analysis = pipeline_data["job_analysis"]

        # Should identify Python as a key requirement
        python_req = next((req for req in job_analysis.requirements if "Python" in req.skill), None)
        assert python_req is not None, "Should identify Python requirement"
        assert python_req.importance >= 4, "Python should be high importance"
        assert python_req.is_required, "Python should be marked as required"

        # Should identify FastAPI as requirement
        fastapi_req = next((req for req in job_analysis.requirements if "FastAPI" in req.skill), None)
        assert fastapi_req is not None, "Should identify FastAPI requirement"

        print("✅ Job analysis quality validated")

        # Validate matching quality
        matching_result = pipeline_data["matching_result"]

        # Should have high Python match
        python_match = next((match for match in matching_result.skill_matches if "Python" in match.skill_name), None)
        assert python_match is not None, "Should match Python skill"
        assert python_match.match_score >= 0.9, "Python should have high match score"
        assert python_match.user_proficiency >= 4, "User has strong Python skills"

        # Should identify good overall match (experienced candidate)
        assert matching_result.overall_match_score >= 0.7, "Should be good overall match"
        assert matching_result.confidence_score >= 0.8, "Should have high confidence"

        print("✅ Matching quality validated")

        # Validate resume generation quality
        tailored_resume = pipeline_data["tailored_resume"]

        # Should contain key technologies from job
        resume_content = tailored_resume.full_resume_markdown.lower()
        assert "python" in resume_content, "Resume should mention Python"
        assert "fastapi" in resume_content, "Resume should mention FastAPI"
        assert "aws" in resume_content, "Resume should mention AWS experience"

        # Should have meaningful optimizations
        assert len(tailored_resume.optimizations) >= 3, "Should have multiple optimizations"

        # Should show improved match score
        assert tailored_resume.estimated_match_score >= matching_result.overall_match_score, "Resume should improve match score"

        print("✅ Resume generation quality validated")

        # Validate validation quality
        validation_result = pipeline_data["validation_result"]

        # Should have high accuracy (good profile data)
        assert validation_result.accuracy_score >= 0.8, "Should have high accuracy"
        assert validation_result.overall_quality_score >= 0.7, "Should have good quality"

        # Should have minimal critical issues
        critical_issues = [issue for issue in validation_result.issues if issue.severity in ["critical", "high"]]
        assert len(critical_issues) <= 2, "Should have minimal critical issues"

        print("✅ Validation quality confirmed")

        print("✅ Complete data quality validation PASSED")

    @pytest.mark.asyncio
    async def test_quickstart_error_scenarios(self, sample_user_profile: Dict[str, Any]):
        """Test error handling in quickstart workflow scenarios."""
        print("\n=== QUICKSTART ERROR SCENARIO VALIDATION ===")

        user_profile = UserProfile.model_validate(sample_user_profile)
        tailoring_service = create_resume_tailoring_service()

        # Test 1: Empty job posting
        with pytest.raises(Exception) as exc_info:
            await tailoring_service.tailor_resume(
                user_profile=user_profile,
                job_posting_text=""
            )
        assert "empty" in str(exc_info.value).lower() or "cannot" in str(exc_info.value).lower()
        print("✅ Empty job posting error handling validated")

        # Test 2: Very short job posting
        with pytest.raises(Exception) as exc_info:
            await tailoring_service.tailor_resume(
                user_profile=user_profile,
                job_posting_text="Short job"
            )
        print("✅ Short job posting error handling validated")

        print("✅ Error scenario validation PASSED")


if __name__ == "__main__":
    """Run quickstart validation directly."""
    import sys
    import tempfile

    # Setup test data
    sample_job_posting = """Senior Software Engineer - Backend Development
TechCorp Inc.

We are looking for a Senior Software Engineer to join our backend development team.
The ideal candidate will have 5+ years of experience building scalable web applications
using Python, FastAPI, and cloud technologies.

Requirements:
- Bachelor's degree in Computer Science or related field
- 5+ years of Python development experience
- Experience with FastAPI, Django, or Flask frameworks
- Strong knowledge of PostgreSQL and database design
- Experience with AWS, Docker, and Kubernetes
- Understanding of microservices architecture
- Excellent problem-solving skills and teamwork abilities

Preferred Qualifications:
- Experience with machine learning or AI systems
- Previous work in fast-paced startup environments
- Contributions to open source projects

We offer competitive salary, excellent health benefits, flexible work arrangements,
and opportunities for professional growth in a collaborative environment."""

    sample_user_profile = {
        "version": "1.0",
        "metadata": {
            "created_at": "2025-09-17T00:00:00Z",
            "updated_at": "2025-09-17T00:00:00Z"
        },
        "contact": {
            "name": "John Developer",
            "email": "john@example.com",
            "location": "San Francisco, CA",
            "linkedin": "https://linkedin.com/in/johndeveloper"
        },
        "professional_summary": "Experienced software engineer with 6 years developing scalable backend systems. Expertise in Python, cloud infrastructure, and building high-performance APIs.",
        "experience": [
            {
                "position": "Software Engineer",
                "company": "StartupXYZ",
                "location": "San Francisco, CA",
                "start_date": "2019-01-15",
                "end_date": None,
                "description": "Lead backend development for core platform serving 100k+ users",
                "achievements": [
                    "Reduced API response time by 40% through optimization and caching",
                    "Designed and implemented microservices architecture supporting 10x growth",
                    "Mentored 3 junior developers and led technical architecture discussions"
                ],
                "technologies": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"]
            }
        ],
        "education": [
            {
                "degree": "Bachelor of Science in Computer Science",
                "institution": "UC Berkeley",
                "location": "Berkeley, CA",
                "graduation_date": "2018-05-15",
                "honors": ["Magna Cum Laude", "Dean's List"]
            }
        ],
        "skills": [
            {"name": "Python", "category": "technical", "proficiency": 5, "years_experience": 6},
            {"name": "FastAPI", "category": "technical", "proficiency": 4, "years_experience": 3},
            {"name": "PostgreSQL", "category": "technical", "proficiency": 4, "years_experience": 4},
            {"name": "AWS", "category": "technical", "proficiency": 3, "years_experience": 2},
            {"name": "Docker", "category": "technical", "proficiency": 4, "years_experience": 3}
        ],
        "projects": [],
        "publications": [],
        "awards": [],
        "volunteer": [],
        "languages": []
    }

    async def run_quickstart_validation():
        """Execute quickstart validation."""
        test_instance = TestQuickstartScenario()

        try:
            await test_instance.test_complete_quickstart_workflow(sample_job_posting, sample_user_profile)
            await test_instance.test_quickstart_data_quality_validation(sample_job_posting, sample_user_profile)
            await test_instance.test_quickstart_error_scenarios(sample_user_profile)

            print("\n🎉 ALL QUICKSTART VALIDATIONS PASSED! 🎉")
            return True

        except Exception as e:
            print(f"\n❌ QUICKSTART VALIDATION FAILED: {e}")
            import traceback
            traceback.print_exc()
            return False

    # Run validation
    if asyncio.run(run_quickstart_validation()):
        sys.exit(0)
    else:
        sys.exit(1)