# Repository Guidelines

## Project Structure
- Backend service lives under `apps/backend/` (FastAPI + Temporal, Python managed by uv).
- Frontend lives under `apps/frontend/` (Svelte + Vite, managed by Bun).
- Shared contracts live under `shared/api-types/`.
- Docker-related configuration lives in `docker/`.

## Build, Test, and Development Commands
- Sync dependencies: `mise run backend.install` / `mise run frontend.install`.
- Start the full stack (Temporal, backend API, worker, frontend): `mise run dev`.
- Backend quality gate: `mise run backend.test backend.lint backend.typecheck`.
- Frontend quality gate: `mise run frontend.test frontend.lint`.
- Regenerate OpenAPI schema + types: `mise run export-openapi && mise run gen-types`.
- Production releases publish a single container (`ghcr.io/<owner>/<repo>`) that serves the SPA from `/` and the API under `/api`.

## Coding Style & Tooling
- Target Python 3.13 with strict type hints; lint & format via Ruff.
- Follow Svelte + TypeScript conventions enforced by ESLint, `svelte-check`, and Vitest.
- Keep commits in Conventional Commit format; CI enforces lint/test on touched workspaces via `.github/workflows/ci.yml`.
- Container builds are defined per-app (`apps/*/Dockerfile`) and orchestrated in `.github/workflows/release.yml`.
