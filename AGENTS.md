# Repository Guidelines

## Project Constitution & Agent Commitments
Review and honor `specify/memory/constitution.md` before any code or planning session. Treat it as the definitive contract for agent conduct: document how your changes uphold the constitution, surface conflicts explicitly, and never bypass guardrails around safety, attribution, or human override. When hand-offs occur, cite relevant clauses so downstream agents inherit the same constraints.

## Project Structure & Module Organization
Core runtime code lives under `src/`, with domain agents in `src/agents/` (job analysis, profile matching, resume generation, validation, human interface). API entry points sit in `src/api/`, orchestration helpers in `src/services/`, shared helpers in `src/utils/`, and structured models in `src/models/`. Tests mirror that layout in `tests/` across unit, integration, e2e, contract, and performance suites. Documentation is under `docs/`, while reusable payloads live in `data/`.

## Build, Test & Development Commands
Bootstrap dependencies using `uv sync --dev`. Launch the FastAPI server with `PYTHONPATH=src uv run python src/main.py`; wrap the command with `infisical run --` whenever secrets are needed. Execute all tests via `PYTHONPATH=src uv run python -m pytest -v`. Keep style checks clean with `uv run ruff format .` and `uv run ruff check .`.

## Coding Style & Naming Conventions
Target Python 3.13 with full type hints on public surfaces. Use 4-space indentation and snake_case for modules, functions, and variables. Agent classes extend `BaseAgent` and follow `<Capability>Agent` naming (e.g., `ResumeGenerationAgent`). Keep FastAPI routes grouped by resource within coherent modules. Let `ruff` enforce formatting and lint rules before opening a PR. Ensure narratives and prompts acknowledge constitutional clauses when behavior might be impacted.

## Testing Guidelines
Pytest is configured via `pytest.ini` with `tests/` as the root. Place happy-path unit specs in `tests/unit/` and interaction checks in `tests/integration/`. Add scenario validations to `tests/e2e/` and schema contracts to `tests/contract/`. Name test functions as `test_<behavior_under_test>`. Constitutional workflows require at least one updated unit and integration test when agents or services change, plus a run of `PYTHONPATH=src infisical run -- uv run python tests/e2e/test_quickstart_scenario.py` before merging.

## Commit & Pull Request Guidelines
Follow Conventional Commits (`feat:`, `fix:`, `docs:`, etc.), mirroring history like `feat: Complete production-ready Resume Assistant with 5-agent chain`. Use imperative subject lines under 72 characters. PRs must summarize scope, list verification commands, reference the constitutional clauses touched, link related specs or issues, and attach API snapshots or logs when behavior shifts. Flag secret-dependent steps so reviewers can reproduce with `infisical`.
