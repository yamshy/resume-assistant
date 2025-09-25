# Repository Guidelines

## Project Structure & Module Organization
Source code lives in `app/`, with Temporal workflows under `app/workflows/`, activities in `app/activities/`, shared state in `app/state.py`, and deterministic utilities in `app/tools/`. The Instructor/OpenAI wrapper sits in `app/tools/llm.py`. FastAPI endpoints are implemented in `app/api/`, the Temporal worker entrypoint is `worker.py`, and `main.py` provides a CLI demo that runs against Temporal's test environment. Tests reside in `tests/` and rely on stub LLM fixtures for deterministic outputs.

## Build, Test, and Development Commands
Always prefer the curated `mise run` tasks so the right environments load. Install dependencies with `mise run backend.install`. Boot the API locally with `mise run backend.dev` (requires a Temporal server) and start the worker via `mise run backend.worker`. Execute the full quality gate before review: `mise run backend.test`, `mise run backend.lint`, and `mise run backend.typecheck`. To validate the containerized stack, use `mise run dev` from the repo root which launches Temporal, the API, the worker, and the frontend.

## Coding Style & Naming Conventions
Target Python 3.13, 4-space indentation, and type-hinted public APIs. Follow `snake_case` for functions, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants. Let the code speak for itself and add comments only when intent is not obvious. `ruff` enforces formatting and linting; keep files ASCII unless there is a clear reason otherwise.

## Testing Guidelines
Use `pytest` with the provided LLM stubs in `tests/`. Name tests after the behavior under check (e.g., `test_workflow_requests_revision`). Prefer exercising activities and Temporal workflows directly. For failure scenarios that hinge on model output, extend the stub LLM to emit deterministic responses. Async tests may rely on `pytest-asyncio`'s auto loop.

## Commit & Pull Request Guidelines
Adopt Conventional Commits (e.g., `feat: wire supervisor graph`). Group related changes and update tests when behavior shifts. PRs should link relevant issues, summarize functional impact, and list the lint/type/test evidence run locally.

## Agent Output Requirements
Agents must always generate a preview when presenting changes or results to users.

## Environment & Configuration Tips
Export `OPENAI_API_KEY` (or load it via your secret manager) before launching the services. Configure Temporal connectivity with `TEMPORAL_HOST` / `TEMPORAL_NAMESPACE`, and swap stub tools for production integrations by constructing a custom `ToolRegistry`. Temporal handles workflow persistence and replay, so no external checkpointer is required.
