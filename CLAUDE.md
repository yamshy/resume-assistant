# Claude Code Context - Resume Assistant

*Auto-generated and manually maintained context for Claude Code*

## Project Overview

**Resume Assistant** - AI-powered resume tailoring system using agent-chain architecture to analyze job postings and generate customized resumes with human-in-the-loop approval workflow.

## Current Feature: Resume Tailoring (001-resume-tailoring-feature)

### Architecture Overview
- **Agent-Chain Pattern**: 5 specialized agents in sequential pipeline
- **Technology Stack**: Python 3.13+, FastAPI, pydanticAI, UV package management
- **Storage**: File-based JSON for single-user profile data
- **Performance Target**: <30 seconds full chain, <5 seconds per agent

### Agent Pipeline
1. **Job Analysis Agent** → Extract requirements from job postings
2. **Profile Matching Agent** → Match user profile against job requirements
3. **Resume Generation Agent** → Create tailored resume content
4. **Validation Agent** → Verify accuracy against source data
5. **Human Interface Agent** → Manage approval workflow

## Active Technologies

- Python 3.13+ with UV package management + FastAPI, pydanticAI, pydantic v2+ (001-resume-tailoring-feature)
- File-based JSON storage for single user profile data (001-resume-tailoring-feature)

## Technology Stack

### Core Dependencies
```python
# FastAPI for HTTP services
fastapi = "^0.104.0"

# pydanticAI for agent implementations
pydantic-ai = "^0.0.14"

# pydantic for data validation
pydantic = "^2.5.0"

# Testing framework
pytest = "^7.4.0"
pytest-asyncio = "^0.21.0"

# Code quality
ruff = "^0.1.0"
```

### Development Tools
- **Package Manager**: UV (for fast dependency management)
- **Code Quality**: ruff (formatting + linting)
- **Testing**: pytest with async support + full mocking
- **CI/CD**: GitHub Actions with UV integration

## Project Structure

```
src/
├── models/           # Pydantic data models
├── agents/           # Individual pydanticAI agents
├── services/         # Service layer (profile management, file I/O)
├── api/             # FastAPI route handlers
└── utils/           # Small utility functions (<30 lines)

tests/
├── unit/            # Individual agent tests with mocks
├── integration/     # Agent chain integration tests
├── contract/        # API contract tests
└── fixtures/        # Test data and mocks

specs/001-resume-tailoring-feature/
├── spec.md          # Feature specification
├── plan.md          # Implementation plan
├── research.md      # Technical research and decisions
├── data-model.md    # Data models and schemas
├── quickstart.md    # End-to-end testing guide
└── contracts/       # API specifications
```

## Constitution Compliance

### ✅ Agent-Chain Architecture (NON-NEGOTIABLE)
- All complex logic implemented as agent chains
- Simple utility functions (<30 lines) for mechanical operations
- Agent input → structured output → next agent pattern

### ✅ FastAPI + pydanticAI Stack
- FastAPI for all HTTP services with async support
- pydanticAI for all agent implementations
- pydantic for comprehensive data validation

### ✅ Test-Driven Development (NON-NEGOTIABLE)
- Tests written before implementation
- All agents mockable without external API dependencies
- Red-Green-Refactor cycle strictly enforced

### ✅ Radical Simplicity (NON-NEGOTIABLE)
- Single-file agents preferred (<200 lines)
- No abstractions until 3rd repetition
- Explainable in 2 sentences: "Agent chain analyzes jobs and tailors resumes with validation"

## Development Patterns

### Agent Implementation Pattern
```python
from pydantic_ai import Agent
from pydantic import BaseModel

# Define structured output
class AgentOutput(BaseModel):
    result: str
    confidence: float

# Initialize agent with type safety (using GPT-4o for all agents)
agent = Agent(
    'openai:gpt-4o',
    output_type=AgentOutput,
    instructions="Agent-specific instructions..."
)

# Use in async pipeline
async def agent_pipeline():
    result = await agent.run(input_data)
    return result.output
```

### Testing Pattern with Mocks
```python
import pytest
from pydantic_ai.models.test import TestModel

@pytest.fixture
def mock_agent():
    return agent.override(model=TestModel())

async def test_agent(mock_agent):
    result = await mock_agent.run("test input")
    assert isinstance(result.output, AgentOutput)
```

### Error Handling Pattern
```python
from pydantic_ai.exceptions import ModelRetry

# Agent-level retry (1-3 attempts before pipeline failure)
@agent.tool
async def validate_output(content: str) -> str:
    if len(content) < 10:
        raise ModelRetry("Content too short, please expand")
    return content
```

## Recent Changes
- 001-resume-tailoring-feature: Added Python 3.13+ with UV package management + FastAPI, pydanticAI, pydantic v2+
- 001-resume-tailoring-feature: Added Python 3.13+ with UV package management + FastAPI, pydanticAI, pydantic v2+

### Current Implementation Status (DEPLOYMENT READY ✅)
- ✅ Feature specification completed and approved
- ✅ Technical research and architecture decisions documented
- ✅ Data models defined with pydantic schemas (27 models)
- ✅ API contracts specified (OpenAPI 3.0)
- ✅ Quickstart guide with end-to-end test scenarios
- ✅ Complete 5-agent chain implemented and validated
- ✅ Full FastAPI application with 8 endpoints
- ✅ Comprehensive test suite (contract, integration, unit, performance)
- ✅ Production utilities (validation, error handling, retry logic)
- ✅ Structural consolidation completed (fixed subagent conflicts)
- ✅ All 49 tasks from tasks.md completed successfully
- ✅ **END-TO-END VALIDATION PASSED** (September 18, 2025)
- ✅ **PRODUCTION DEPLOYMENT APPROVED** (Performance: 65-110s, Quality: 85%)

### Technology Decisions
- **Model Selection**: GPT-4o for all agents (cost management)
- **Profile Setup**: Simple JSON template (no guided flows)
- **Validation Thresholds**: >0.8 confidence auto-approve, <0.6 triggers human review
- **Error Recovery**: 1-3 retries per agent before pipeline failure
- **Resume Format**: Chronological with AI-driven relevance highlighting

### When Adding New Code
1. **Agents for intelligence**: Any "understanding", "analyzing", or "reasoning" → use pydanticAI agent
2. **Scripts for mechanics**: Simple data transformation, file I/O, config loading → small Python functions
3. **Test everything**: Mock external dependencies, focus on agent behavior and integration
4. **Keep it simple**: Single-file agents, clear interfaces, no premature abstractions

### Performance Considerations
- Use parallel execution for independent operations (job analysis + profile validation)
- Reuse agent instances across requests
- GPT-4o across all agents for consistency
- Stream results for long-running operations

### File Locations
- **Profile data**: `~/.resume-assistant/profile.json`
- **Session temp data**: `~/.resume-assistant/sessions/`
- **Final resumes**: `~/.resume-assistant/exports/`
- **Logs**: Structured JSON to stderr, no sensitive data

---

*Context maintained for agent-chain resume tailoring implementation*
*Constitution v1.1.0 | Feature 001 | Phase 1 Complete*
*Last updated: 2025-09-17*