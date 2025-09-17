# Resume Assistant Constitution

## Core Principles

### I. Agent-Chain Architecture (NON-NEGOTIABLE)
**ALL features are agent chains, not traditional code.** Every task = agent takes input → produces structured output → feeds next agent. No complex parsing scripts, regex systems, or traditional data processing. When you think "I need to parse this" → use an agent. When you think "I need to analyze this" → use an agent. Agents chain together to solve complex problems through simple, focused steps.

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

### Allowed Non-Agent Code
**Small, focused Python scripts are allowed to avoid wasting tokens on trivial operations:**
- **Simple data models** (pydantic schemas for API contracts)
- **Thin FastAPI route handlers** (just invoke agents, no business logic)
- **Basic utility functions** (file I/O, simple transformations < 20 lines)
- **Test fixtures and mocks** (for agent testing)
- **Configuration loading** (environment variables, settings)
- **Small cleanup scripts** (format data between agent calls, < 30 lines)
- **Trivial data transformations** (string formatting, list operations, dict merging)
- **Simple file operations** (read/write JSON, basic validation)

**Rules:**
- **Must be tightly scoped** (single purpose, < 30 lines)
- **No complex logic** (no nested conditionals, loops over complex data)
- **No "intelligence"** (if it requires decision-making → use an agent)
- **Token efficiency** (don't use agents for trivial string formatting)

**Rule of thumb**: If it involves "understanding", "analyzing", or "reasoning" → use an agent. If it's mechanical data manipulation → script is fine.

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

### Traditional Code Red Flags
- ❌ **Complex parsing scripts** (>30 lines, use parsing agents instead)
- ❌ **Regex systems for content analysis** (use analysis agents for understanding)
- ❌ **Large data transformation pipelines** (use agent chains for complex logic)
- ❌ **BeautifulSoup/lxml for content extraction** (use extraction agents for understanding)
- ❌ **Complex rule-based systems** (use reasoning agents for decisions)
- ❌ **Large validation logic** (>20 lines, use validation agents)

### Overengineering Red Flags
- ❌ Abstract factories for simple data creation
- ❌ Repository patterns for single data source
- ❌ Complex inheritance hierarchies for agents
- ❌ Middleware layers without clear necessity
- ❌ Configuration frameworks for simple settings
- ❌ Event systems for direct function calls
- ❌ Generic interfaces with only one implementation

### Agent-First Enforcement
- ✅ **Agent chains over traditional processing**
- ✅ **Structured output agents over parsing scripts**
- ✅ **Small focused agents over monolithic functions**
- ✅ **AI reasoning over rule-based logic**
- ✅ **Natural language understanding over regex patterns**
- ✅ **Agent orchestration over pipeline frameworks**
- ✅ **Single file per agent until it exceeds 200 lines**

## Governance

Constitution supersedes all other practices. Amendments require documentation, approval, and migration plan. All development must verify compliance with these principles.

**Complexity Justification Required**: Any deviation from simplicity must include a written justification explaining why simpler alternatives are insufficient.

Use `/CLAUDE.md` for runtime development guidance and agent implementation patterns.

**Version**: 1.1.0 | **Ratified**: 2025-09-17 | **Last Amended**: 2025-09-17

## Amendment History
- **v1.1.0** (2025-09-17): Clarified agent-chain architecture with balanced approach allowing small focused scripts
- **v1.0.0** (2025-09-17): Initial constitution for resume assistant project