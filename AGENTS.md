# Repository Guidelines

## Project Structure & Module Organization
Source code lives in `app/` with LangGraph-native packages such as `graphs/`, `state.py`, and `tools/`. `tools/llm.py` wraps the OpenAI chat model via LangChain, while `tools/vector.py`, `tools/cache.py`, and `tools/notifications.py` expose deterministic utilities. The LangGraph server configuration resides in `langgraph.json`; `main.py` offers a CLI demo. Tests live under `tests/`, relying on stub LLMs for deterministic assertions.

## Build, Test, and Development Commands
Install dependencies once with:
```bash
uv sync
```
Run the LangGraph server during development (requires `OPENAI_API_KEY` in scope):
```bash
uv run langgraph server start --config langgraph.json --host 0.0.0.0 --port 8124
```
Quality gates to run before review:
```bash
uv run pytest
uv run --extra dev ruff check
uv run --extra dev mypy app
```
Use `docker compose up --build` to run the LangGraph Server container with an optional Redis checkpointer.

## Coding Style & Naming Conventions
Keep Python 3.12, 4-space indentation, `snake_case` functions, `PascalCase` classes, and `UPPER_SNAKE_CASE` constants. Public interfaces should remain type hinted. Comment sparingly: prefer self-explanatory code.

## Testing Guidelines
Write `pytest` tests in `tests/`. Prefer exercising compiled graphs and LLM stubs directly instead of crafting HTTP tests. When negative paths require model output, extend the stub LLM to produce deterministic responses. Async code may rely on `pytest-asyncio`'s auto event loop configuration.

## Commit & Pull Request Guidelines
Use Conventional Commits (e.g., `feat: wire llm drafting subgraph` or `fix: tighten compliance prompt`). Group related changes and include updated tests. PRs should link issues, describe functional shifts, highlight configuration updates, and document lint/type/test evidence.

## Environment & Configuration Tips
Provide `OPENAI_API_KEY` (optionally via Infisical) when running the supervisor graph. Replace the stub tooling in tests with production equivalents by constructing a custom `ToolRegistry`. Attach a persistent checkpointer (Redis, Postgres, LangGraph Cloud) through `compile_supervisor_graph(checkpointer=...)` to unlock run replay and HITL pauses. Keep secrets out of commits; rely on the team’s preferred secret manager.
