# Resume Assistant Constitution

## Core Principles

### I. Agent-First Architecture
Every feature starts as an independent AI agent or service component. Agents must be self-contained, independently testable, and have clearly defined responsibilities. No monolithic agents - each agent serves a specific purpose in the resume generation workflow.

### II. FastAPI + pydanticAI Stack
All services built using FastAPI with pydantic for data validation and pydanticAI for agent implementations. Microservice architecture with clear API contracts. Text I/O protocol: JSON in/out via REST APIs, structured logging to stderr.

### III. Test-Driven Development (NON-NEGOTIABLE)
TDD mandatory: Specs written → User approved → Tests fail → Then implement. Red-Green-Refactor cycle strictly enforced. All agents must be mockable for testing without external API dependencies.

### IV. Data Integrity & Validation
Focus areas requiring validation: User data store integrity, Resume content accuracy against source data, Job posting analysis correctness, Inter-agent communication contracts. A dedicated validator agent prevents hallucinations.

### V. Human-in-the-Loop Design
AI agents can request clarification from users when needed. Clear escalation paths defined. Observability through structured logging and agent decision tracking. User approval gates for final resume output.

### VI. Latest Technology & Documentation
Always use latest versions of FastAPI, pydantic, pydanticAI, and Python. Reference official documentation via web or context. UV for Python package management. No legacy compatibility requirements.

### VII. Radical Simplicity (NON-NEGOTIABLE)
Start with the simplest solution that works. YAGNI principles strictly enforced. No abstractions until you need them 3+ times. Single-file agents preferred over complex hierarchies. Flat is better than nested. If you can't explain it in 2 sentences, it's too complex.

## Agent Architecture

### Core Agents Required
- **Job Analysis Agent**: Parses and extracts requirements from job postings
- **Resume Generation Agent**: Creates tailored resume content
- **Validation Agent**: Ensures accuracy against user data store
- **Data Store Agent**: Manages structured user profile data
- **Human Interface Agent**: Handles clarification requests and approvals

### Data Flow
Job Posting → Job Analysis → Resume Generation → Validation → Human Review → Final Output

## Technology Standards

### Required Stack
- **Runtime**: Python 3.13+ with UV package management
- **Web Framework**: FastAPI for all HTTP services
- **AI Framework**: pydanticAI for all agent implementations
- **Data Validation**: pydantic v2+ for all schemas
- **Testing**: pytest with async support, full mocking of external APIs
- **Code Quality**: ruff for formatting and linting
- **CI/CD**: GitHub Actions with uv integration

### Deployment
- Containerized microservices
- Environment-based configuration
- Health check endpoints required
- Structured JSON logging

## Development Workflow

### Specification-Driven Development
1. Write detailed specs for each agent and API
2. Create tests based on specs (must fail initially)
3. Implement minimum viable functionality
4. Refactor while maintaining green tests
5. Document API contracts and agent behaviors

### Quality Gates
- All tests must pass
- No external API dependencies in tests
- Ruff formatting and linting clean
- Type hints required for all public interfaces
- Integration tests for agent workflows

## Anti-Patterns (Forbidden)

### Overengineering Red Flags
- ❌ Abstract factories for simple data creation
- ❌ Repository patterns for single data source
- ❌ Complex inheritance hierarchies for agents
- ❌ Middleware layers without clear necessity
- ❌ Configuration frameworks for simple settings
- ❌ Event systems for direct function calls
- ❌ Generic interfaces with only one implementation

### Simplicity Enforcement
- ✅ Direct function calls over event systems
- ✅ Simple classes over complex patterns
- ✅ Inline logic over premature abstractions
- ✅ Copy-paste acceptable until 3rd repetition
- ✅ Single file per agent until it exceeds 200 lines
- ✅ Environment variables over configuration frameworks

## Governance

Constitution supersedes all other practices. Amendments require documentation, approval, and migration plan. All development must verify compliance with these principles.

**Complexity Justification Required**: Any deviation from simplicity must include a written justification explaining why simpler alternatives are insufficient.

Use `/CLAUDE.md` for runtime development guidance and agent implementation patterns.

**Version**: 1.0.0 | **Ratified**: 2025-09-17 | **Last Amended**: 2025-09-17