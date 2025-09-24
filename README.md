# Resume Assistant

The Resume Assistant now runs on a Temporal + FastAPI backend, coordinating durable workflow execution with human-in-the-loop approvals while preserving the original resume generation logic. Instructor continues to power schema-validated LLM interactions, and the deterministic tool suite (vector search, renderer, cache, notifications) remains unchanged.

## Architecture Overview
- **Temporal Workflow (`app/workflows/resume.py`)** orchestrates ingestion → drafting → critique → compliance → publishing with automatic retries and persistent state. Human approval gates rely on Temporal signals and `workflow.wait_condition`.
- **Activities (`app/activities/`)** encapsulate all side-effecting work—LLM calls, vector indexing, cache writes, and notifications. Each activity exposes a Pydantic input/output schema and reuses the existing `ToolRegistry` implementation.
- **FastAPI (`app/api/`)** exposes REST endpoints to start workflows, query state, submit approvals, and fetch results using the Temporal client.
- **Worker (`worker.py`)** registers workflows and activities with Temporal and executes the business logic in a separate process.

## Requirements
- Python 3.12+
- Running Temporal service (local development uses the Docker Compose stack below)
- `OPENAI_API_KEY` available for production LLM runs.

## Quick Start
1. Install dependencies:
   ```bash
   uv sync
   ```
2. Run the CLI demo against Temporal's time-skipping test environment:
   ```bash
   uv run python main.py
   ```
   The script prints audit events, the published resume preview, cache contents, and notifications from a full workflow execution.

## Testing & Tooling
Deterministic unit and integration tests leverage the Temporal test environment and the stub LLM:
```bash
uv run pytest
```
Optional quality gates remain available:
```bash
uv run --extra dev ruff check
uv run --extra dev mypy app
```

## Configuration
- Adjust `AgentConfig` (`app/state.py`) to tweak revision budgets, default model identifiers, or compliance blocklists.
- Override tooling by constructing a custom `ToolRegistry` and passing it to `configure_registry` before starting the worker.
- Set `TEMPORAL_HOST` / `TEMPORAL_NAMESPACE` to target a remote Temporal cluster.

## Docker Support
Two build targets share the same codebase and dependencies:
```bash
docker compose up --build
```
- `temporal` boots a self-contained Temporal server (SQLite-backed) on port `7233`.
- `api` serves the FastAPI application on port `8080`.
- `worker` registers workflows/activities and executes jobs pulled from Temporal.

## Development Notes
- Instructor response models continue to guarantee structured LLM outputs for planning, drafting, critique, and compliance.
- `tests/stubs.StubResumeLLM` powers deterministic tests; production environments rely on `OpenAIResumeLLM`.
- Audit trails, metrics, and artifact management remain identical to the LangGraph implementation, now persisted through Temporal workflow history.

## Contributing
Follow Conventional Commits (e.g., `feat: integrate temporal workflow`) and include updated tests when behaviour changes. Surface evidence of lint, type-check, and test runs in pull requests to keep CI green.
