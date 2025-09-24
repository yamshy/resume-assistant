# LangGraph Resume Assistant

The Resume Assistant now runs as an agentic LangGraph application driven entirely by LLM reasoning. Every stage—planning, drafting, critique, and compliance—delegates text-heavy work to an OpenAI-backed model instrumented with Instructor for schema-validated outputs, while thin Python tools provide deterministic storage, vector search, and notification utilities.

## Architecture Overview
- **Supervisor StateGraph** routes requests across modular subgraphs and enforces revision budgets with LangGraph checkpointing support.
- **Ingestion Subgraph** normalises raw documents and upserts them into the vector index for later retrieval.
- **Drafting Subgraph** calls the Instructor-wrapped LLM to build a plan and generate the full markdown resume, folding in retrieval hits and profile context.
- **Critique Subgraph** leverages the LLM to decide whether additional revisions are required, annotating telemetry with the true revision count.
- **Compliance Subgraph** revisits the LLM with policy guidance (blocklists, tone hints) to approve or reject publication.
- **Publishing Subgraph** persists artifacts and emits operational notifications; it is deliberately deterministic to keep side effects auditable.

## Requirements
- Python 3.12+
- `OPENAI_API_KEY` available in the environment (Infisical, `.env`, or shell export). The agents will raise an error if a key is missing when invoked.

## Quick Start
1. Install dependencies:
   ```bash
   uv sync
   ```
2. Launch the LangGraph server (requires the OpenAI key in scope):
   ```bash
   uv run langgraph server start --config langgraph.json --host 0.0.0.0 --port 8124
   ```
   The server exposes the compiled supervisor graph under the identifier `resume-supervisor`.
3. Exercise the workflow locally:
   ```bash
   uv run python main.py
   ```
   `main.py` seeds representative artifacts and prints the audit trail, published resume, cache entry, and notifications from a single run.

## Testing & Tooling
Deterministic unit tests rely on a stub LLM so they can run without network calls:
```bash
uv run pytest
```
Optional quality gates remain available:
```bash
uv run --extra dev ruff check
uv run --extra dev mypy app
```

## Configuration
- Update `AgentConfig` (`app/state.py`) to tweak revision limits, default model tags, or compliance blocklists.
- Swap tooling implementations by constructing a custom `ToolRegistry` (e.g., plugging in production vector stores or cache layers) and passing it to `build_supervisor`.
- Integrate LangGraph checkpoint persistence (Redis, Postgres, LangGraph Cloud) via `compile_supervisor_graph(checkpointer=...)`.

## Docker Support
The container image ships the LangGraph server directly:
```bash
docker compose up --build
```
- `langgraph` serves the supervisor on port `8124`.
- The optional Redis service is ready for attaching a persistent LangGraph checkpointer.
Provide `OPENAI_API_KEY` (and any other model credentials) via your preferred secret manager before starting the stack.

## Development Notes
- Complex text analysis, reasoning, and drafting are handled exclusively by the Instructor-validated LLM. Python functions stay focused on data access, storage, or lightweight transformations.
- `OpenAIResumeLLM` uses Instructor response models to guarantee structured outputs for planning, critique, compliance, and drafting while automatically retrying invalid generations.
- Tests use `tests/stubs.StubResumeLLM` to simulate LLM responses deterministically; production runs automatically pivot to the OpenAI-backed `OpenAIResumeLLM`.
- All telemetry (draft counts, revision totals, audit trails) flows through LangGraph reducers to keep dashboards honest.

## Contributing
Follow Conventional Commits (e.g., `feat: integrate llm critique agent`) and include updated tests when behaviour changes. Surface evidence of lint, type-check, and test runs in pull requests to keep CI green.
