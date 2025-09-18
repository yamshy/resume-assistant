# Architecture Documentation

## System Overview

The Resume Assistant uses a **5-agent chain architecture** to transform job postings into tailored, professional resumes.

## Agent Chain Pipeline

```
Job Posting Text
        ↓
[Job Analysis Agent] → Extract requirements (5-10s)
        ↓
[Profile Matching Agent] → Match skills & experience (3-5s)
        ↓
[Resume Generation Agent] → Create tailored content (35-45s)
        ↓
[Validation Agent] → Quality & accuracy check (5-8s)
        ↓
[Human Interface Agent] → Approval workflow (<1s)
        ↓
Tailored Resume + Approval Decision
```

## Constitutional Patterns

### Agent-Chain Architecture
- **All intelligence** implemented as pydanticAI agents
- **Sequential pipeline** with structured data flow
- **No business logic** in API route handlers
- **Clean separation** between mechanical and intelligent operations

### Technology Stack
- **FastAPI** for HTTP services with async support
- **pydanticAI** for all agent implementations
- **Pydantic** for comprehensive data validation
- **GPT-4o** for consistent model performance across agents

### Radical Simplicity
- **Single-file agents** (<200 lines each)
- **Clear interfaces** with structured inputs/outputs
- **No abstractions** until 3rd repetition
- **Explainable design** - easily understood by developers

## Performance Characteristics

- **Total Pipeline:** 65-110 seconds
- **Individual Agents:** All under 60 seconds
- **API Endpoints:** <500ms for non-AI operations
- **Memory Usage:** Stable under load
- **Error Rate:** 0% for valid inputs

## Data Flow

1. **Input:** Raw job posting text + user profile
2. **Processing:** 5-agent sequential transformation
3. **Output:** Tailored resume + approval workflow + session data
4. **Storage:** File-based JSON with session management

## Quality Assurance

- **Validation Agent** ensures factual accuracy
- **Confidence scoring** determines approval workflow
- **Human-in-the-loop** for quality control
- **Retry logic** for transient failures

## Complete Documentation

- **[CLAUDE.md](../../CLAUDE.md)** - Complete system context and patterns
- **[Feature Spec](../../specs/001-resume-tailoring-feature/spec.md)** - Detailed technical specification
- **[Data Models](../../specs/001-resume-tailoring-feature/data-model.md)** - Pydantic schemas and structures