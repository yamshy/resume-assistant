# Repository Guidelines

## Project Structure & Module Organization
Source code lives in `app/`, with Temporal workflows under `app/workflows/`, activities in `app/activities/`, shared state in `app/state.py`, and deterministic utilities in `app/tools/`. The Instructor/OpenAI wrapper sits in `app/tools/llm.py`. FastAPI endpoints are implemented in `app/api/`, the Temporal worker entrypoint is `worker.py`, and `main.py` provides a CLI demo that runs against Temporal's test environment. Tests reside in `tests/` and rely on stub LLM fixtures for deterministic outputs.

## Build, Test, and Development Commands
Run `uv sync` once to install dependencies. Boot the API locally with `uv run uvicorn app.api:app --reload` (requires a Temporal server) or start the CLI demo via `uv run python main.py`. Execute the full quality gate before review: `uv run pytest`, `uv run --extra dev ruff check`, and `uv run --extra dev mypy app`. To validate the containerized stack, use `docker compose up --build` which launches Temporal, the API, and the worker.

## Coding Style & Naming Conventions
Target Python 3.12, 4-space indentation, and type-hinted public APIs. Follow `snake_case` for functions, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants. Let the code speak for itself and add comments only when intent is not obvious. `ruff` enforces formatting and linting; keep files ASCII unless there is a clear reason otherwise.

## Testing Guidelines
Use `pytest` with the provided LLM stubs in `tests/`. Name tests after the behavior under check (e.g., `test_workflow_requests_revision`). Prefer exercising activities and Temporal workflows directly. For failure scenarios that hinge on model output, extend the stub LLM to emit deterministic responses. Async tests may rely on `pytest-asyncio`'s auto loop.

## Commit & Pull Request Guidelines
Adopt Conventional Commits (e.g., `feat: wire supervisor graph`). Group related changes and update tests when behavior shifts. PRs should link relevant issues, summarize functional impact, and list the lint/type/test evidence run locally.

## Agent Output Requirements
Agents must always generate a preview when presenting changes or results to users.

## Environment & Configuration Tips
Export `OPENAI_API_KEY` (or load it via your secret manager) before launching the services. Configure Temporal connectivity with `TEMPORAL_HOST` / `TEMPORAL_NAMESPACE`, and swap stub tools for production integrations by constructing a custom `ToolRegistry`. Temporal handles workflow persistence and replay, so no external checkpointer is required.
