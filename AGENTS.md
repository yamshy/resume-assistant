# Repository Guidelines

## Project Structure & Module Organization
Source code lives in `app/`, with domain modules such as `generator.py`, `router.py`, and integrations like `vectorstore.py`. UI assets ship from `app/frontend` and require no build step. The FastAPI entrypoint is `main.py`, while reusable fixtures and API checks reside in `tests/`. Docker assets (`Dockerfile`, `docker-compose.yml`) let you run the API, Redis, and Chroma-backed services locally.

## Build, Test, and Development Commands
Install dependencies once with:
```bash
uv sync
```
Run the API during development:
```bash
uv run uvicorn main:app --reload
```
Quality gates must pass before review:
```bash
uv run pytest
uv run --extra dev ruff check
uv run --extra dev mypy app
```
Use `docker compose up --build` when you need the full stack (API + Redis + Chroma) wired together.

## Coding Style & Naming Conventions
Target Python 3.12 and follow 4-space indentation. Modules and functions use `snake_case`, classes remain in `PascalCase`, and constants in `UPPER_SNAKE_CASE`. Maintain type hints on new public interfaces. Ruff enforces import hygiene and basic linting; run `uv run --extra dev ruff check --fix` for mechanical cleanups, but keep manual refactors separate from feature work. Align docstrings with NumPy-style summaries when documenting public methods.

## Testing Guidelines
Write tests in `tests/` using `pytest` conventions (`test_*.py` files, `Test*` classes optional). Cover new behaviours with focused unit tests and favour deterministic fixtures over live service calls; `fakeredis` is available for cache-dependent logic. Async code is auto-handled by `pytest-asyncio`, so mark coroutines with `async def` and let the plugin manage the event loop. Ensure negative paths are exercised alongside the happy path before opening a pull request.

## Commit & Pull Request Guidelines
Use Conventional Commits such as `feat: add resume caching metrics` or `fix: handle empty knowledge store`. Group related changes into a single commit to keep the history searchable. Pull requests should link relevant issues, summarise the change, and call out any configuration updates. Always include evidence that lint, type checks, and tests ran (command output or checklist) and describe any manual QA performed.

## Environment & Configuration Tips
Set `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` to reach real LLM backends; otherwise the service falls back to the deterministic template generator. The knowledge store persists to `data/knowledge/knowledge_store.json` by default—override the location with the `KNOWLEDGE_STORE_PATH` environment variable when running multiple sandboxes. Keep credentials out of commits and share secrets via team-approved managers.
