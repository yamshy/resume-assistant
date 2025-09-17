# Research: Resume Tailoring Agent Architecture

*Generated during Phase 0 of implementation planning*

## Agent-Chain Architecture Patterns

### Decision: PydanticAI Programmatic Hand-off Pattern
**Rationale**: For resume tailoring, we need sequential processing where each agent's output feeds into the next. The programmatic hand-off pattern provides clear control flow and allows for error handling between each step.

**Implementation Pattern**:
```python
async def resume_tailoring_pipeline(job_desc: str, user_profile: dict):
    # Agent 1: Job Analysis Agent
    job_analysis = await job_analyzer.run(job_desc)

    # Agent 2: Profile Matching Agent
    match_result = await profile_matcher.run({
        "job_requirements": job_analysis.output,
        "user_profile": user_profile
    })

    # Agent 3: Resume Generation Agent
    tailored_resume = await resume_generator.run({
        "job_analysis": job_analysis.output,
        "match_result": match_result.output,
        "user_profile": user_profile
    })

    # Agent 4: Validation Agent
    validation = await validator.run({
        "original_profile": user_profile,
        "tailored_resume": tailored_resume.output,
        "job_requirements": job_analysis.output
    })

    # Agent 5: Human Interface Agent (approval workflow)
    approval_request = await human_interface.run({
        "validation_result": validation.output,
        "changes_made": tailored_resume.output,
        "confidence_scores": validation.output.accuracy_score
    })

    return approval_request.output
```

**Alternatives considered**:
- Agent delegation pattern (more complex, harder to test)
- Graph-based control flow (overkill for linear workflow)

## Structured Input/Output with Pydantic Schemas

### Decision: Strongly typed schemas for all inter-agent communication
**Rationale**: Ensures data integrity, provides clear contracts, enables easy testing and validation.

**Core Data Models**:
```python
class JobRequirement(BaseModel):
    skill: str = Field(description="Required skill or qualification")
    importance: int = Field(ge=1, le=5, description="Importance level 1-5")
    category: str = Field(description="Skill category (technical, soft, etc.)")

class JobAnalysis(BaseModel):
    requirements: List[JobRequirement]
    company_culture: str
    role_level: str
    industry: str
    key_responsibilities: List[str]

class MatchingResult(BaseModel):
    skill_matches: List[Dict[str, float]]
    experience_alignment: float
    missing_skills: List[str]
    strength_areas: List[str]
    recommendations: List[str]

class ResumeOptimization(BaseModel):
    section: str  # summary, experience, skills, education
    original_content: str
    optimized_content: str
    match_score: float = Field(ge=0, le=1)
    reasoning: str

class ValidationResult(BaseModel):
    is_valid: bool
    accuracy_score: float = Field(ge=0, le=1)
    issues: List[str]
    suggestions: List[str]

class ApprovalRequest(BaseModel):
    changes: List[ResumeOptimization]
    confidence_score: float
    requires_human_review: bool
    review_reasons: List[str]
    final_resume_markdown: str
```

**Alternatives considered**:
- Dict-based communication (lacks validation, error-prone)
- Simple string passing (loses structure, harder to process)

## Testing Strategy with Mocks

### Decision: TestModel and FunctionModel for comprehensive testing
**Rationale**: Allows testing agent logic without external API calls, ensures fast and reliable tests.

**Testing Approach**:
```python
# Unit tests for individual agents
@pytest.fixture
def mock_job_analyzer():
    return job_analyzer.override(model=TestModel())

# Integration tests with FunctionModel for predictable responses
def mock_job_analysis_response(messages):
    return JobAnalysis(
        requirements=[
            JobRequirement(skill="Python", importance=5, category="technical"),
            JobRequirement(skill="FastAPI", importance=4, category="technical")
        ],
        company_culture="collaborative",
        role_level="senior",
        industry="technology",
        key_responsibilities=["Build APIs", "Code review"]
    )

# Full pipeline testing
async def test_full_pipeline():
    with (
        job_analyzer.override(model=FunctionModel(mock_job_analysis_response)),
        profile_matcher.override(model=TestModel()),
        resume_generator.override(model=TestModel()),
        validator.override(model=TestModel()),
        human_interface.override(model=TestModel())
    ):
        result = await resume_tailoring_pipeline("job desc", {"profile": "data"})
        assert result is not None
```

**Alternatives considered**:
- Real API calls in tests (slow, flaky, expensive)
- Manual mocking (complex, hard to maintain)

## Error Handling and Resilience

### Decision: Retry with exponential backoff + Circuit breaker pattern
**Rationale**: Resume generation is time-sensitive but not critical infrastructure, so we balance reliability with cost.

**Implementation Strategy**:
```python
# Retry configuration for transient failures
transport = AsyncTenacityTransport(
    config=RetryConfig(
        retry=retry_if_exception_type(HTTPStatusError),
        wait=wait_exponential(multiplier=1, max=60),
        stop=stop_after_attempt(3),  # Conservative for cost control
        reraise=True
    )
)

# Circuit breaker for agent health
class AgentCircuitBreaker:
    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 30):
        # Implementation details...
```

**Alternatives considered**:
- No retry logic (poor user experience on transient failures)
- Aggressive retries (expensive, may hit rate limits)

## Performance Optimization Strategy

### Decision: Parallel processing where possible + Agent reuse
**Rationale**: 30-second target requires optimization, but simplicity is prioritized over complex caching.

**Optimization Approaches**:
1. **Parallel Independent Operations**: Job analysis and profile loading can run in parallel
2. **Agent Instance Reuse**: Initialize agents once, reuse across requests
3. **Model Selection**: Use faster models (gpt-4o-mini) for validation, premium models (claude-sonnet-4) for content generation
4. **Streaming Results**: For long resume generation, stream partial results to UI

```python
# Parallel processing example
async def optimized_analysis(job_desc: str, user_profile: dict):
    job_task = asyncio.create_task(job_analyzer.run(job_desc))
    profile_validation_task = asyncio.create_task(validate_profile(user_profile))

    job_result, profile_validation = await asyncio.gather(job_task, profile_validation_task)
    # Continue with dependent operations...
```

**Alternatives considered**:
- Complex caching systems (overengineering for single-user system)
- Synchronous processing (too slow for 30s target)

## Technology Stack Decisions

### Decision: FastAPI + pydanticAI + File-based JSON storage
**Rationale**: Aligns with constitution requirements, provides type safety, fast development cycle.

**Stack Justification**:
- **FastAPI**: Constitutional requirement, excellent async support, auto-generated docs
- **pydanticAI**: Constitutional requirement, type-safe AI framework, great testing support
- **File-based JSON**: Simple for single-user system, easy to backup/restore, no database overhead
- **pytest with async**: Industry standard, excellent mocking support

### Decision: Model Selection Strategy
**Rationale**: Balance cost, speed, and quality based on task complexity.

**Model Allocation**:
- **Job Analysis Agent**: GPT-4o (complex reasoning, high accuracy needed)
- **Profile Matching Agent**: GPT-4o (complex comparison logic)
- **Resume Generation Agent**: Claude Sonnet 4 (superior content generation)
- **Validation Agent**: GPT-4o-mini (simple validation, cost-effective)
- **Human Interface Agent**: GPT-4o-mini (simple workflow decisions)

**Alternatives considered**:
- Single model for all agents (suboptimal cost/performance balance)
- Local models (complexity, hardware requirements)

## File Storage Schema Design

### Decision: Structured JSON with versioning
**Rationale**: Easy to read/write, supports schema evolution, simple backup/restore.

**Profile Storage Structure**:
```json
{
  "version": "1.0",
  "metadata": {
    "created_at": "2025-09-17T00:00:00Z",
    "updated_at": "2025-09-17T00:00:00Z"
  },
  "profile": {
    "contact": {
      "name": "string",
      "email": "string",
      "phone": "string",
      "location": "string"
    },
    "summary": "string",
    "experience": [...],
    "education": [...],
    "skills": {
      "technical": [...],
      "soft": [...]
    },
    "optional_sections": {
      "projects": [...],
      "publications": [...],
      "awards": [...],
      "volunteer": [...],
      "languages": [...]
    }
  }
}
```

**Alternatives considered**:
- Database storage (overkill for single user)
- YAML format (less standard for API data)

## Security and Privacy Considerations

### Decision: Local file storage + input sanitization
**Rationale**: Single-user system minimizes attack surface, local storage provides data control.

**Security Measures**:
- Input sanitization for job posting text
- Structured logging without sensitive data
- Local file permissions for profile data
- No external data transmission (except to AI APIs)

**Alternatives considered**:
- Cloud storage (unnecessary privacy risk for personal data)
- Database encryption (overkill for local single-user system)

## Development and Testing Infrastructure

### Decision: UV + pytest + ruff + GitHub Actions
**Rationale**: Modern Python toolchain, fast package management, comprehensive testing.

**Development Workflow**:
1. UV for dependency management and virtual environments
2. pytest for all testing (unit, integration, contract)
3. ruff for formatting and linting
4. GitHub Actions for CI/CD
5. Docker for containerized deployment

**Alternatives considered**:
- pip + virtualenv (slower, less modern)
- Different test frameworks (pytest is standard and excellent)

---

*Research complete - all technical unknowns resolved for Phase 1 design*