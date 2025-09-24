# Repository Guidelines

## Project Structure & Module Organization
Source code lives in `app/`, with graphs kept under `app/graphs/`, shared state in `app/state.py`, and deterministic utilities in `app/tools/`. The LangChain/OpenAI wrapper sits in `app/tools/llm.py`. Configuration for the LangGraph server is defined in `langgraph.json`, and `main.py` offers a CLI demo. Tests reside in `tests/` and rely on stub LLM fixtures for deterministic outputs.

## Build, Test, and Development Commands
Run `uv sync` once to install dependencies. Start the local LangGraph server with `uv run langgraph server start --config langgraph.json --host 0.0.0.0 --port 8124` (needs `OPENAI_API_KEY`). Execute the full quality gate before review: `uv run pytest`, `uv run --extra dev ruff check`, and `uv run --extra dev mypy app`. To validate the containerized stack, use `docker compose up --build`.

## Coding Style & Naming Conventions
Target Python 3.12, 4-space indentation, and type-hinted public APIs. Follow `snake_case` for functions, `PascalCase` for classes, and `UPPER_SNAKE_CASE` for constants. Let the code speak for itself and add comments only when intent is not obvious. `ruff` enforces formatting and linting; keep files ASCII unless there is a clear reason otherwise.

## Testing Guidelines
Use `pytest` with the provided LLM stubs in `tests/`. Name tests after the behavior under check (e.g., `test_supervisor_handles_pause`). Prefer executing compiled graphs directly instead of HTTP layers. For failure scenarios that hinge on model output, extend the stub LLM to emit deterministic responses. Async tests may rely on `pytest-asyncio`'s auto loop.

## Commit & Pull Request Guidelines
Adopt Conventional Commits (e.g., `feat: wire supervisor graph`). Group related changes and update tests when behavior shifts. PRs should link relevant issues, summarize functional impact, and list the lint/type/test evidence run locally.

## Environment & Configuration Tips
Export `OPENAI_API_KEY` (or load it via your secret manager) before launching the server. Swap stub tools for production integrations by constructing a custom `ToolRegistry`. Attach a persistent checkpointer—Redis, Postgres, or LangGraph Cloud—when calling `compile_supervisor_graph(checkpointer=...)` to enable run replay and HITL pauses.
