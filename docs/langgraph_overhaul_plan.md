# LangGraph Overhaul Plan for Resume Assistant

## 1. Objectives & Guardrails
- **Agent-first orchestration**: Replace bespoke planner/executor classes with LangGraph agents that are responsible for reasoning, routing, and invoking tools. All multi-step reasoning must be delegated to agents, avoiding brittle regex-based control flow.
- **Modular graph topology**: Model ingestion, enrichment, resume synthesis, validation, and delivery as composable LangGraph subgraphs to improve reliability, observability, and testability.
- **Deterministic interfaces**: Transition public traffic to the LangGraph Server HTTP API so the frontend can rely on the LangGraph SDK. Ensure new components are typed, testable, and respect existing caching, auditing, and compliance requirements.
- **Single-step switchover**: Plan for a one-time cutover to the LangGraph-driven AI agent, retiring legacy orchestration the moment the new stack is verified end-to-end.
- **Complete repository overhaul**: Authorize the AI implementation agent to replace or delete any legacy module, asset, or configuration that does not support the LangGraph architecture; the final tree must contain only the new stack.

## 2. Current State Snapshot
- Custom `ResumeGenerationAgent`, `ResumeIngestionAgent`, and related helpers encapsulate workflows with imperative Python logic, synchronous retries, and manual state machines.
- Tools (vector store, knowledge base, document parser, template renderer) are invoked directly without shared agent context or memory primitives.
- Monitoring, validation, and human-in-the-loop (HITL) checkpoints are ad hoc, making it difficult to pause, inspect, or replay runs.

## 3. Target LangGraph Architecture

### 3.1 High-Level Graph Topology
```
Client → LangGraph Server HTTP API
              │
              ▼
    Supervisor Agent (Router)
                   /            |              \
                  ▼             ▼               ▼
        Ingestion Subgraph   Resume Drafting   Insights & QA Subgraph
                                 │                    │
                                 ▼                    ▼
                        Revision & Critique Loop   Compliance Agent
                                 │                    │
                                 └──────► Publishing & Notification ─────► Outputs / Cache
```
- **Supervisor Agent**: LangGraph `StateGraph` with a router node deciding which specialized subgraph handles a request (ingest, draft, regenerate, fetch insights).
- **Subgraphs**: Each functional area is implemented as its own graph with dedicated state schema and memory strategy. Subgraphs communicate via structured messages rather than shared globals.
- **Revision Loop**: Uses LangGraph’s conditional edges to iterate draft → critique → revise until quality thresholds met or HITL intervention triggered.

### 3.2 State Design
- Define a base `ConversationState` dataclass capturing `messages`, `artifacts` (documents, embeddings), `audit_trail`, and `metrics` counters. Use reducers for additive properties (e.g., metrics) to avoid concurrent update conflicts.
- Configure `MemorySaver` (short-term) plus vector-backed store (long-term) for cross-thread recall of resumes and feedback. Persist states via Postgres or Redis checkpointing depending on deployment.

### 3.3 Agents & Tooling
- **Ingestion Agent**: Wraps document loaders, text normalization, and metadata extraction as LangChain tools. Replace regex-based parsing with LLM classification and structured extraction using Instructor/Pydantic schemas.
- **Drafting Agent**: Primary creative agent that calls models (OpenAI, Anthropic). Tools: template selector, skill taxonomy retriever, knowledge base search, formatting assistant.
- **Critique Agent**: Evaluates drafts using evaluation criteria prompts, optionally leveraging LangSmith evaluators. Can request human review via LangGraph `interrupt()`.
- **Compliance Agent**: Ensures redaction policies, job description alignment, and brand tone compliance using checklists encoded as evaluation prompts.
- **Publishing Node**: Handles persistence, cache updates, and notifications; mostly deterministic logic but receives structured inputs from agents.

### 3.4 Human-in-the-Loop Strategy
- Implement breakpoints before final publishing and after major critiques. Use LangGraph HITL APIs to allow operations staff to approve revisions or supply additional context.
- Support time-travel debugging for incident response and to reproduce problematic outputs.

### 3.5 Observability & Evaluation
- Integrate LangSmith tracing with custom tags for each agent/subgraph.
- Adopt LangGraph streaming to expose intermediate reasoning in the UI.
- Establish evaluation harness using LangSmith AgentEvals on representative datasets to measure win rates vs. legacy system.

## 4. Component Refactor Map

| Area | Legacy Modules | LangGraph Replacement | Notes |
| --- | --- | --- | --- |
| API Entry | `main.py`, `router.py` | Replace FastAPI app with LangGraph Server deployment (`langgraph.json`, assistants) | Route traffic through LangGraph Server endpoints so clients consume the SDK. |
| Orchestration | `generator.py`, `ingestion/` | `graphs/supervisor.py`, `graphs/ingestion.py`, `graphs/generation.py` | Each graph compiles to callable interface with `invoke`/`astream`. |
| Tools | `vectorstore.py`, `resume_builder.py` | `tools/vector.py`, `tools/render.py`, etc. using LangChain tool wrappers | Ensure idempotent operations for retries. |
| Caching | `cache.py` | Shared service invoked by Publishing node; implement as tool to keep agent-mediated control. |
| Monitoring | Custom logs | LangSmith instrumentation + structured events from graph runs | Standardize metadata schema. |

## 5. Full Switchover Execution Plan

The AI implementation agent must complete every step below before the system is activated. No dual-run or legacy fallback is permitted once the cutover occurs.

1. **LangGraph Stack Assembly**
   - Add LangGraph and LangSmith dependencies, create the `graphs/` package, and implement shared state models and reducers.
   - Implement ingestion, drafting, critique, compliance, and publishing subgraphs end-to-end with deterministic tests verifying parity against fixtures representing current production behaviours.
   - Establish the Supervisor Agent as the single orchestration entrypoint, wiring all subgraphs through structured state transitions.

2. **Tooling & Infrastructure Hardening**
   - Wrap all existing tools (vector store, knowledge base, renderer, cache, notifications) as LangChain tools with idempotent semantics and explicit error handling.
   - Configure LangGraph Server with authentication, persistence (Redis/Postgres checkpoints), and streaming hooks; bake configuration into `langgraph.json` and deployment manifests.
   - Instrument LangSmith tracing, metrics emission, and HITL breakpoints; provide dashboards and operational runbooks.

3. **Verification Gauntlet**
   - Execute regression tests covering ingestion, drafting, revision loop, compliance, publishing, and caching interactions using `pytest` and LangSmith AgentEvals.
   - Run load and soak tests against LangGraph Server to validate latency, throughput, and checkpoint integrity; capture acceptance thresholds in the runbook.
   - Review HITL flows in staging, ensuring interrupts, approvals, and resumption paths function without manual intervention from legacy components.

4. **One-Time Cutover**
   - Update FastAPI entrypoints to proxy exclusively to LangGraph Server, deprecating legacy orchestration classes and routes.
   - Migrate deployment infrastructure (Docker, CI/CD) to ship the LangGraph configuration and remove references to superseded modules.
   - Execute a controlled production deploy, monitor telemetry for two business days, and confirm success criteria before declaring completion.

5. **Post-Switchover Repo Hygiene**
   - Purge the repository of deprecated orchestration code, configs, Docker artifacts, and scripts; confirm `app/`, `tests/`, and deployment manifests reference only LangGraph components.
   - Rebuild documentation, onboarding guides, and architecture diagrams so they exclusively describe the LangGraph system; remove outdated guidance.
   - Transition ongoing maintenance workflows (prompt updates, tool additions) to the Supervisor Agent governance process and record a retrospective capturing the overhaul.

## 6. Risk Mitigation & Open Questions
- **Tool determinism**: Ensure tool functions are idempotent; add caching layers or guardrails where side effects occur.
- **Model drift**: Leverage LangGraph assistants to version prompts and configurations per deployment stage.
- **Performance**: Profile graph execution; use parallel branches cautiously to avoid `INVALID_CONCURRENT_GRAPH_UPDATE` errors.
- **Ops readiness**: Train support team on LangGraph Studio for debugging and HITL workflows.
- **Open questions**:
  - Decide on checkpoint backend (Redis vs. Postgres) for production scale.
  - Determine if we need specialized agents for analytics/insights beyond resume workflows.
  - Evaluate feasibility of migrating evaluation harness to LangGraph-managed cron jobs for continuous testing.

## 7. Deliverables
- LangGraph-based code modules, configuration (`langgraph.json`), and deployment automation.
- LangGraph Server deployment replacing FastAPI entrypoint with no legacy rollback path.
- Repository tree scrubbed of legacy orchestration assets, with lint/type/test pipelines updated for the LangGraph stack only.
- Documentation: developer guides, operational runbooks, and user-facing changelog entries.
- Comprehensive regression suite covering ingestion, generation, compliance, and publishing flows.
