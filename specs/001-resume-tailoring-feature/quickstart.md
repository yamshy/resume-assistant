# Quickstart Guide: Resume Tailoring System

*Generated during Phase 1 of implementation planning*

## Overview

This guide demonstrates the complete resume tailoring workflow from job posting analysis to final approved resume generation using our 5-agent chain architecture.

## Prerequisites

- Python 3.13+ with UV package management
- FastAPI application running on localhost:8000
- User profile data already configured in the system

## Quick Test Scenario

### Test Data Setup

**Sample Job Posting** (save as `test_job.txt`):
```
Senior Software Engineer - Backend Development
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
and opportunities for professional growth in a collaborative environment.
```

**Sample User Profile Data** (minimal for testing):
```json
{
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
      "end_date": null,
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
```

## Step-by-Step Workflow Test

### 1. Health Check
```bash
curl -X GET "http://localhost:8000/health"
```

**Expected Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-09-17T10:00:00Z"
}
```

### 2. Setup User Profile
```bash
curl -X PUT "http://localhost:8000/profile" \
  -H "Content-Type: application/json" \
  -d @user_profile.json
```

**Expected Response**: User profile echoed back with validation confirmation.

### 3. Analyze Job Posting
```bash
curl -X POST "http://localhost:8000/jobs/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Senior Software Engineer - Backend Development\nTechCorp Inc.\n\nWe are looking for a Senior Software Engineer..."
  }'
```

**Expected Response** (Job Analysis Agent output):
```json
{
  "company_name": "TechCorp Inc.",
  "job_title": "Senior Software Engineer - Backend Development",
  "location": "Not specified",
  "requirements": [
    {
      "skill": "Python",
      "importance": 5,
      "category": "technical",
      "is_required": true,
      "context": "5+ years of Python development experience"
    },
    {
      "skill": "FastAPI",
      "importance": 4,
      "category": "technical",
      "is_required": true,
      "context": "Experience with FastAPI, Django, or Flask frameworks"
    }
  ],
  "key_responsibilities": [
    "Building scalable web applications",
    "Backend development",
    "Working with cloud technologies"
  ],
  "company_culture": "collaborative environment",
  "role_level": "senior",
  "industry": "technology"
}
```

### 4. Generate Tailored Resume (Full Chain)
```bash
curl -X POST "http://localhost:8000/resumes/tailor" \
  -H "Content-Type: application/json" \
  -d '{
    "job_description": "Senior Software Engineer - Backend Development\nTechCorp Inc.\n\nWe are looking for a Senior Software Engineer...",
    "preferences": {
      "emphasis_areas": ["Python", "FastAPI", "AWS"],
      "excluded_sections": []
    }
  }'
```

**Expected Response** (Full Agent Chain Result):
```json
{
  "resume_id": "550e8400-e29b-41d4-a716-446655440000",
  "job_analysis": { /* JobAnalysis from step 3 */ },
  "matching_result": {
    "overall_match_score": 0.85,
    "skill_matches": [
      {
        "skill_name": "Python",
        "job_importance": 5,
        "user_proficiency": 5,
        "match_score": 1.0,
        "evidence": ["6 years Python experience", "FastAPI expertise"]
      }
    ],
    "missing_requirements": [
      {
        "skill": "Kubernetes",
        "importance": 3,
        "category": "technical"
      }
    ],
    "recommendations": [
      "Highlight experience with scalable systems",
      "Emphasize mentoring and leadership experience"
    ]
  },
  "tailored_resume": {
    "job_title": "Senior Software Engineer - Backend Development",
    "company_name": "TechCorp Inc.",
    "optimizations": [
      {
        "section": "summary",
        "original_content": "Experienced software engineer with 6 years developing scalable backend systems...",
        "optimized_content": "Senior Software Engineer with 6+ years building scalable backend systems using Python and FastAPI. Proven track record in microservices architecture and cloud technologies...",
        "optimization_reason": "Emphasized senior level and exact technology match",
        "keywords_added": ["Senior", "microservices architecture", "cloud technologies"],
        "match_improvement": 0.15
      }
    ],
    "full_resume_markdown": "# John Developer\n\n**Senior Software Engineer**\n...",
    "summary_of_changes": "Enhanced professional summary to emphasize senior-level experience and exact technology matches. Highlighted microservices architecture experience and leadership qualities.",
    "estimated_match_score": 0.85,
    "generation_timestamp": "2025-09-17T10:05:00Z"
  },
  "validation_result": {
    "is_valid": true,
    "accuracy_score": 0.95,
    "readability_score": 0.88,
    "keyword_optimization_score": 0.82,
    "issues": [],
    "strengths": [
      "Strong keyword alignment with job requirements",
      "Quantified achievements maintained accuracy",
      "Natural language flow preserved"
    ],
    "overall_quality_score": 0.88,
    "validation_timestamp": "2025-09-17T10:05:30Z"
  },
  "approval_workflow": {
    "requires_human_review": false,
    "review_reasons": [],
    "confidence_score": 0.88,
    "auto_approve_eligible": true
  }
}
```

### 5. Human Approval (if required)
```bash
curl -X POST "http://localhost:8000/resumes/550e8400-e29b-41d4-a716-446655440000/approve" \
  -H "Content-Type: application/json" \
  -d '{
    "decision": "approved",
    "feedback": "Looks great! The emphasis on microservices experience is perfect for this role.",
    "approved_sections": ["summary", "experience", "skills", "education"]
  }'
```

**Expected Response**:
```json
{
  "status": "approved",
  "final_resume_url": "http://localhost:8000/resumes/550e8400-e29b-41d4-a716-446655440000/download",
  "revision_needed": false,
  "next_steps": [
    "Download your tailored resume",
    "Review final formatting",
    "Submit your application to TechCorp Inc."
  ]
}
```

### 6. Download Final Resume
```bash
curl -X GET "http://localhost:8000/resumes/550e8400-e29b-41d4-a716-446655440000/download?format=markdown" \
  -o "tailored_resume_techcorp.md"
```

**Expected Response**: Markdown file containing the final tailored resume.

## Agent Chain Verification

### Performance Expectations
- **Total Chain Time**: < 30 seconds for complete workflow
- **Individual Agent Times**:
  - Job Analysis Agent: < 5 seconds
  - Profile Matching Agent: < 3 seconds
  - Resume Generation Agent: < 10 seconds
  - Validation Agent: < 5 seconds
  - Human Interface Agent: < 2 seconds

### Quality Validation Checkpoints

1. **Job Analysis Quality**:
   - All key requirements extracted with correct importance ratings
   - Company culture and role level correctly identified
   - Technical skills properly categorized

2. **Matching Accuracy**:
   - Overall match score reflects actual skill alignment
   - Missing requirements clearly identified
   - Recommendations are actionable and specific

3. **Resume Optimization**:
   - Original content preserved where appropriate
   - Keywords naturally integrated (not stuffed)
   - Quantified achievements maintained
   - Professional tone and readability preserved

4. **Validation Effectiveness**:
   - No factual inaccuracies introduced
   - Keyword optimization balanced with readability
   - Quality scores align with manual review

5. **Approval Workflow**:
   - Auto-approval triggers only for high-confidence results
   - Human review requested for appropriate edge cases
   - Clear feedback mechanisms for iterative improvement

## Error Handling Verification

### Test Error Scenarios

1. **Invalid Job Description**:
```bash
curl -X POST "http://localhost:8000/jobs/analyze" \
  -H "Content-Type: application/json" \
  -d '{"job_description": ""}'
```
**Expected**: 400 error with helpful message

2. **Missing Profile Data**:
```bash
curl -X POST "http://localhost:8000/resumes/tailor" \
  -H "Content-Type: application/json" \
  -d '{"job_description": "Test job"}'
# When no profile exists
```
**Expected**: 404 error requesting profile setup

3. **Agent Timeout**:
Test with very long job description to trigger timeout handling.

## Integration Test Success Criteria

✅ **All API endpoints respond correctly**
✅ **Agent chain completes within 30 seconds**
✅ **Generated resume maintains factual accuracy (>95% validation score)**
✅ **Keyword optimization balanced with readability (>80% scores)**
✅ **Approval workflow triggers appropriately**
✅ **Error handling graceful for all failure modes**
✅ **Final resume downloadable in requested format**

## Troubleshooting

### Common Issues

1. **Agent Timeout**: Check model availability and network connectivity
2. **Low Match Scores**: Verify job description quality and profile completeness
3. **Validation Failures**: Review agent output for factual inconsistencies
4. **Approval Workflow Issues**: Check confidence thresholds and review logic

### Log Analysis
```bash
# Check structured logs for agent chain execution
tail -f logs/resume-assistant.log | grep "agent_execution"

# Monitor performance metrics
curl http://localhost:8000/metrics
```

---

*Quickstart complete - ready for test-driven development implementation*