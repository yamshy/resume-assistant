
# Implementation Plan: Resume Tailoring Feature

**Branch**: `001-resume-tailoring-feature` | **Date**: 2025-09-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-resume-tailoring-feature/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Fill the Constitution Check section based on the content of the constitution document.
4. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
5. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
6. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, `GEMINI.md` for Gemini CLI, `QWEN.md` for Qwen Code or `AGENTS.md` for opencode).
7. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
8. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
9. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Resume tailoring feature that uses an agent-chain architecture to analyze job postings, match them against user profile data, and generate customized resumes. The system employs 5 specialized agents: Job Analysis Agent (extracts requirements), Profile Matching Agent (finds relevant data), Resume Generation Agent (creates tailored content), Validation Agent (ensures accuracy), and Human Interface Agent (handles approval workflow). Built with FastAPI endpoints and pydanticAI agents for comprehensive human-in-the-loop resume customization.

## Technical Context
**Language/Version**: Python 3.13+ with UV package management
**Primary Dependencies**: FastAPI, pydanticAI, pydantic v2+
**Storage**: File-based JSON storage for single user profile data
**Testing**: pytest with async support, full mocking of external APIs
**Target Platform**: Linux server, containerized microservices
**Project Type**: single - web API backend with FastAPI endpoints
**Performance Goals**: <30 seconds for full agent chain resume generation, individual agent responses <5 seconds
**Constraints**: Single user system, no external API dependencies in tests, mockable agent implementations
**Scale/Scope**: Personal resume assistant, 5 core agents, structured data validation with pydantic schemas

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**I. Agent-Chain Architecture**: ✓
- [x] Feature implemented as agent chain for complex logic
- [x] Agent steps: input → structured output → feeds next agent
- [x] Small Python scripts (<30 lines) allowed for trivial operations
- [x] Any "understanding" or "reasoning" delegated to agents

**II. FastAPI + pydanticAI Stack**: ✓
- [x] FastAPI used for HTTP services
- [x] pydanticAI used for agent implementations
- [x] pydantic used for data validation
- [x] JSON in/out via REST APIs

**III. Test-Driven Development**: ✓
- [x] Tests written before implementation
- [x] All agents mockable without external APIs
- [x] Red-Green-Refactor cycle planned

**IV. Data Integrity & Validation**: ✓
- [x] Validation agent included if data accuracy critical
- [x] Inter-agent contracts defined
- [x] Data store integrity maintained

**V. Human-in-the-Loop Design**: ✓
- [x] Clarification mechanisms defined if needed
- [x] User approval gates identified
- [x] Structured logging for observability

**VI. Latest Technology**: ✓
- [x] Python 3.13+ and uv package management
- [x] Latest versions of FastAPI, pydantic, pydanticAI
- [x] Official documentation referenced

**VII. Radical Simplicity**: ✓
- [x] Simplest solution that works chosen
- [x] No abstractions until 3rd repetition
- [x] Single-file agents preferred (< 200 lines)
- [x] No overengineering patterns (see anti-patterns list)
- [x] Can explain entire feature in 2 sentences

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure]
```

**Structure Decision**: Option 1 (Single project) - FastAPI backend with agent-based architecture

## Phase 0: Outline & Research
1. **Extract unknowns from Technical Context** above:
   - For each NEEDS CLARIFICATION → research task
   - For each dependency → best practices task
   - For each integration → patterns task

2. **Generate and dispatch research agents**:
   ```
   For each unknown in Technical Context:
     Task: "Research {unknown} for {feature context}"
   For each technology choice:
     Task: "Find best practices for {tech} in {domain}"
   ```

3. **Consolidate findings** in `research.md` using format:
   - Decision: [what was chosen]
   - Rationale: [why chosen]
   - Alternatives considered: [what else evaluated]

**Output**: research.md with all NEEDS CLARIFICATION resolved

## Phase 1: Design & Contracts
*Prerequisites: research.md complete*

1. **Extract entities from feature spec** → `data-model.md`:
   - Entity name, fields, relationships
   - Validation rules from requirements
   - State transitions if applicable

2. **Generate API contracts** from functional requirements:
   - For each user action → endpoint
   - Use standard REST/GraphQL patterns
   - Output OpenAPI/GraphQL schema to `/contracts/`

3. **Generate contract tests** from contracts:
   - One test file per endpoint
   - Assert request/response schemas
   - Tests must fail (no implementation yet)

4. **Extract test scenarios** from user stories:
   - Each story → integration test scenario
   - Quickstart test = story validation steps

5. **Update agent file incrementally** (O(1) operation):
   - Run `.specify/scripts/bash/update-agent-context.sh claude` for your AI assistant
   - If exists: Add only NEW tech from current plan
   - Preserve manual additions between markers
   - Update recent changes (keep last 3)
   - Keep under 150 lines for token efficiency
   - Output to repository root

**Output**: data-model.md, /contracts/*, failing tests, quickstart.md, agent-specific file

## Phase 2: Task Planning Approach
*This section describes what the /tasks command will do - DO NOT execute during /plan*

**Task Generation Strategy**:
- Load `.specify/templates/tasks-template.md` as base
- Generate tasks from Phase 1 design docs (contracts, data model, quickstart)
- Each contract → contract test task [P]
- Each entity → model creation task [P] 
- Each user story → integration test task
- Implementation tasks to make tests pass

**Ordering Strategy**:
- TDD order: Tests before implementation 
- Dependency order: Models before services before UI
- Mark [P] for parallel execution (independent files)

**Estimated Output**: 25-30 numbered, ordered tasks in tasks.md

**IMPORTANT**: This phase is executed by the /tasks command, NOT by /plan

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |


## Progress Tracking
*This checklist is updated during execution flow*

**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (/plan command - describe approach only)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved
- [ ] Complexity deviations documented

---
*Based on Constitution v1.1.0 - See `.specify/memory/constitution.md`*
