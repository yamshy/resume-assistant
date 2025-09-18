# Tasks: Resume Tailoring Feature

**Input**: Design documents from `/specs/001-resume-tailoring-feature/`
**Prerequisites**: research.md, data-model.md, contracts/api_spec.yaml, quickstart.md

## Execution Flow (main)
```
1. Load research.md → Extract: tech stack (FastAPI, pydanticAI, UV), agent architecture
2. Load data-model.md → Extract: 11 entities → model tasks
3. Load contracts/api_spec.yaml → Extract: 7 endpoints → contract test tasks
4. Load quickstart.md → Extract: 6 integration scenarios → integration test tasks
5. Generate tasks by category:
   → Setup: project init, dependencies, linting
   → Tests: contract tests, integration tests (TDD)
   → Core: agent implementations, models, services
   → Integration: API endpoints, file storage
   → Polish: unit tests, performance validation
6. Apply task rules:
   → Different files = mark [P] for parallel
   → Same file = sequential (no [P])
   → Tests before implementation (TDD)
```

## Format: `[ID] [P?] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- Include exact file paths in descriptions

## Phase 3.1: Setup

- [ ] T001 Create project structure (src/, tests/, specs/) per implementation plan
- [ ] T002 Initialize Python 3.13+ project with UV and FastAPI dependencies
- [ ] T003 [P] Configure ruff for linting and formatting in pyproject.toml
- [ ] T004 [P] Setup pytest with async support in pyproject.toml

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE 3.3

**CRITICAL: These tests MUST be written and MUST FAIL before ANY implementation**

### Contract Tests (API Endpoints)
- [ ] T005 [P] Contract test GET /health in tests/contract/test_health.py
- [ ] T006 [P] Contract test GET /profile in tests/contract/test_profile.py
- [ ] T007 [P] Contract test PUT /profile in tests/contract/test_profile.py
- [ ] T008 [P] Contract test POST /jobs/analyze in tests/contract/test_jobs.py
- [ ] T009 [P] Contract test POST /resumes/tailor in tests/contract/test_resumes.py
- [ ] T010 [P] Contract test POST /resumes/{id}/approve in tests/contract/test_approval.py
- [ ] T011 [P] Contract test GET /resumes/{id}/download in tests/contract/test_download.py

### Integration Tests (Agent Chain Scenarios)
- [ ] T012 [P] Integration test complete agent chain workflow in tests/integration/test_agent_chain.py
- [ ] T013 [P] Integration test job analysis agent performance in tests/integration/test_job_analysis.py
- [ ] T014 [P] Integration test profile matching accuracy in tests/integration/test_profile_matching.py
- [ ] T015 [P] Integration test resume generation quality in tests/integration/test_resume_generation.py
- [ ] T016 [P] Integration test validation agent effectiveness in tests/integration/test_validation.py
- [ ] T017 [P] Integration test approval workflow automation in tests/integration/test_approval_workflow.py

## Phase 3.3: Core Implementation (ONLY after tests are failing)

### Data Models (Pydantic Schemas)
- [ ] T018 [P] UserProfile and related models in src/models/profile.py
- [ ] T019 [P] JobAnalysis and JobRequirement models in src/models/job_analysis.py
- [ ] T020 [P] MatchingResult and SkillMatch models in src/models/matching.py
- [ ] T021 [P] TailoredResume and ContentOptimization models in src/models/resume.py
- [ ] T022 [P] ValidationResult and ValidationIssue models in src/models/validation.py
- [ ] T023 [P] ApprovalWorkflow and ReviewDecision models in src/models/approval.py

### pydanticAI Agents (Core Intelligence)
- [ ] T024 [P] Job Analysis Agent with GPT-4o in src/agents/job_analysis_agent.py
- [ ] T025 [P] Profile Matching Agent with GPT-4o in src/agents/profile_matching_agent.py
- [ ] T026 [P] Resume Generation Agent with Claude Sonnet 4 in src/agents/resume_generation_agent.py
- [ ] T027 [P] Validation Agent with GPT-4o-mini in src/agents/validation_agent.py
- [ ] T028 [P] Human Interface Agent with GPT-4o-mini in src/agents/human_interface_agent.py

### Service Layer
- [ ] T029 [P] Profile management service with JSON file storage in src/services/profile_service.py
- [ ] T030 [P] Resume generation pipeline service in src/services/resume_service.py
- [ ] T031 [P] File storage service for sessions and exports in src/services/storage_service.py

### Agent Chain Pipeline
- [ ] T032 Resume tailoring pipeline orchestrating 5 agents in src/services/resume_service.py

## Phase 3.4: Integration (API Endpoints)

- [ ] T033 Health check endpoint in src/api/health.py
- [ ] T034 Profile endpoints (GET/PUT /profile) in src/api/profile.py
- [ ] T035 Job analysis endpoint (POST /jobs/analyze) in src/api/jobs.py
- [ ] T036 Resume tailoring endpoint (POST /resumes/tailor) in src/api/resumes.py
- [ ] T037 Approval workflow endpoints (/resumes/{id}/approve) in src/api/approval.py
- [ ] T038 Resume download endpoint (GET /resumes/{id}/download) in src/api/download.py
- [ ] T039 Resume history endpoint (GET /resumes/history) in src/api/history.py
- [ ] T040 FastAPI application setup and middleware in src/main.py

## Phase 3.5: Polish

### Error Handling & Validation
- [ ] T041 [P] Input validation and error handling in src/utils/validation.py
- [ ] T042 [P] API error responses and logging in src/utils/errors.py
- [ ] T043 [P] Agent retry logic with exponential backoff in src/utils/retry.py

### Performance & Quality
- [ ] T044 [P] Unit tests for agent mocking in tests/unit/test_agent_mocks.py
- [ ] T045 [P] Performance validation (<30s full chain) in tests/performance/test_timing.py
- [ ] T046 [P] Data validation and schema tests in tests/unit/test_models.py

### Final Validation
- [ ] T047 End-to-end quickstart scenario validation per quickstart.md
- [ ] T048 Manual testing of all API endpoints with sample data
- [ ] T049 Performance tuning and optimization review

## Dependencies

### Sequential Dependencies
- Setup (T001-T004) blocks all other phases
- Tests (T005-T017) MUST complete before implementation (T018-T040)
- Models (T018-T023) block Agents (T024-T028)
- Agents (T024-T028) block Services (T029-T032)
- Services (T029-T032) block API endpoints (T033-T040)
- Core implementation blocks Polish (T041-T049)

### Specific Blocking Relationships
- T018 (UserProfile) blocks T029 (ProfileService)
- T019 (JobAnalysis) blocks T024 (JobAnalysisAgent)
- T024-T028 (all agents) block T030 (ResumeService)
- T030 (ResumeService) blocks T036 (ResumeTailoringEndpoint)

## Parallel Execution Examples

### Contract Tests (Run together after setup)
```
Task: "Contract test GET /health in tests/contract/test_health.py"
Task: "Contract test GET /profile in tests/contract/test_profile.py"
Task: "Contract test PUT /profile in tests/contract/test_profile.py"
Task: "Contract test POST /jobs/analyze in tests/contract/test_jobs.py"
```

### Data Models (Run together after tests)
```
Task: "UserProfile and related models in src/models/profile.py"
Task: "JobAnalysis and JobRequirement models in src/models/job_analysis.py"
Task: "MatchingResult and SkillMatch models in src/models/matching.py"
Task: "TailoredResume and ContentOptimization models in src/models/resume.py"
```

### pydanticAI Agents (Run together after models)
```
Task: "Job Analysis Agent with GPT-4o in src/agents/job_analysis_agent.py"
Task: "Profile Matching Agent with GPT-4o in src/agents/profile_matching_agent.py"
Task: "Resume Generation Agent with Claude Sonnet 4 in src/agents/resume_generation_agent.py"
Task: "Validation Agent with GPT-4o-mini in src/agents/validation_agent.py"
```

## Notes

- **Agent-Chain Focus**: All intelligence implemented as pydanticAI agents, not scripts
- **Test-Driven Development**: Red-Green-Refactor cycle strictly enforced
- **Performance Target**: <30 seconds for complete 5-agent chain
- **Model Selection**: GPT-4o for analysis, Claude Sonnet 4 for generation, GPT-4o-mini for validation
- **Storage**: File-based JSON for single-user profile and session data
- **Error Handling**: Retry with exponential backoff, graceful degradation
- **Parallel Tasks [P]**: Different files, no shared dependencies
- **Agent Testing**: Use TestModel and FunctionModel for mocking external API calls

## Validation Checklist

- [x] All API endpoints have contract tests (T005-T011)
- [x] All entities have model tasks (T018-T023)
- [x] All agents have implementation tasks (T024-T028)
- [x] All integration scenarios have tests (T012-T017)
- [x] Tests come before implementation (Phase 3.2 → 3.3)
- [x] Parallel tasks are truly independent
- [x] Each task specifies exact file path
- [x] Agent chain architecture properly decomposed into 5 specialized agents

---

*Task generation complete - ready for test-driven development implementation*