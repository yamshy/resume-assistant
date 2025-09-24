# LangGraph Overhaul Plan for Resume Assistant

## 1. Objectives & Guardrails
- **Agent-first orchestration**: Replace bespoke planner/executor classes with LangGraph agents that are responsible for reasoning, routing, and invoking tools. All multi-step reasoning must be delegated to agents, avoiding brittle regex-based control flow.
- **Modular graph topology**: Model ingestion, enrichment, resume synthesis, validation, and delivery as composable LangGraph subgraphs to improve reliability, observability, and testability.
- **Deterministic interfaces**: Maintain our FastAPI surface while swapping the underlying execution layer. Ensure new components are typed, testable, and respect existing caching, auditing, and compliance requirements.
- **Gradual rollout**: Support dual-mode execution (legacy + LangGraph) during migration, enabling phased cut-over and feature parity validation.

## 2. Current State Snapshot
- Custom `ResumeGenerationAgent`, `ResumeIngestionAgent`, and related helpers encapsulate workflows with imperative Python logic, synchronous retries, and manual state machines.
- Tools (vector store, knowledge base, document parser, template renderer) are invoked directly without shared agent context or memory primitives.
- Monitoring, validation, and human-in-the-loop (HITL) checkpoints are ad hoc, making it difficult to pause, inspect, or replay runs.

## 3. Target LangGraph Architecture

### 3.1 High-Level Graph Topology
```
Client → FastAPI Router → LangGraph App
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
| API Entry | `main.py`, `router.py` | Add LangGraph app startup & thread management | Continue to serve FastAPI routes; inject LangGraph client. |
| Orchestration | `generator.py`, `ingestion/` | `graphs/supervisor.py`, `graphs/ingestion.py`, `graphs/generation.py` | Each graph compiles to callable interface with `invoke`/`astream`. |
| Tools | `vectorstore.py`, `resume_builder.py` | `tools/vector.py`, `tools/render.py`, etc. using LangChain tool wrappers | Ensure idempotent operations for retries. |
| Caching | `cache.py` | Shared service invoked by Publishing node; implement as tool to keep agent-mediated control. |
| Monitoring | Custom logs | LangSmith instrumentation + structured events from graph runs | Standardize metadata schema. |

## 5. Migration Phases

1. **Foundation (Week 1-2)**
   - Introduce LangGraph dependencies and scaffolding (`graphs/` package, shared state models, base tools).
   - Implement ingestion subgraph end-to-end with parity tests against legacy pipeline.
   - Wire FastAPI route flag to choose legacy vs. LangGraph execution for ingestion flows.

2. **Drafting & Revision (Week 3-4)**
   - Build drafting and critique subgraphs with revision loop.
   - Add HITL checkpoints and streaming support.
   - Implement evaluator-based regression suite comparing draft quality metrics to baseline.

3. **Compliance & Publishing (Week 5)**
   - Integrate compliance agent and publishing node.
   - Migrate caching, notifications, and auditing into LangGraph tools.
   - Run load tests to validate checkpoint persistence & scaling characteristics.

4. **Supervisor & Multi-Agent Routing (Week 6)**
   - Introduce supervisor router controlling subgraph hand-offs.
   - Enable time-travel debugging, finalize LangSmith dashboards, and document operational runbooks.
   - Switch production default to LangGraph path with rollback toggle.

5. **Decommission Legacy (Week 7)**
   - Remove deprecated orchestration classes, clean configs, and update developer documentation.
   - Conduct post-mortem to capture lessons and finalize architecture diagrams.

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
- Updated FastAPI integration with feature flag and fallbacks.
- Documentation: developer guides, operational runbooks, and user-facing changelog entries.
- Comprehensive regression suite covering ingestion, generation, compliance, and publishing flows.

