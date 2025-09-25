# Resume Assistant Monorepo

This repository hosts the full Resume Assistant stack:

- **apps/backend** – FastAPI + Temporal orchestration layer implemented in Python and managed with [`uv`](https://github.com/astral-sh/uv).
- **apps/frontend** – Svelte + Vite user interface, built and tested with [Bun](https://bun.sh/).
- **shared/api-types** – Generated OpenAPI schema and TypeScript bindings shared across services.
- **docker/** – Docker Compose definitions used for local development and future production variants.

The layout keeps each app self-contained (native manifests, lockfiles, Dockerfiles) while providing thin coordination at the root
level via `.mise.toml` tasks for common workflows.

## Getting Started

1. **Install prerequisites**
   - Docker & Docker Compose
   - Python 3.13 (or install via `mise`)
   - Bun `1.1.27`
   - uv (installed automatically by `mise` or via `pip install uv`)
   - Trust the task definitions once per machine: `mise trust .mise.toml`

2. **Sync dependencies**
   ```bash
   mise run backend.install
   mise run frontend.install
   ```

3. **Start the full stack**
   ```bash
   mise run dev
   ```
   This launches Temporal, the FastAPI API, the Temporal worker, and the Bun/Vite dev server. The backend listens on
   `http://localhost:8124/api`, the frontend on `http://localhost:5173`.

4. **Run tests**
   ```bash
   mise run backend.test
   mise run frontend.test
   ```

## API Schema & Shared Types

Regenerate the FastAPI OpenAPI schema and TypeScript client types whenever backend endpoints change:

```bash
mise run export-openapi
mise run gen-types
```

The schema is written to `shared/api-types/openapi.json`; frontend types live at `apps/frontend/src/lib/api/types.ts`.

## Container Images

The release workflow builds a single image that bundles the FastAPI API, Temporal worker, and the compiled Svelte frontend:

- `Dockerfile` compiles the Svelte app with Bun, syncs backend dependencies with `uv`, and launches both the API and
  Temporal worker in one container. Static frontend assets are served from `/`, and the API remains available under `/api`.

Local development containers live under `docker/docker-compose.dev.yml`, which still runs the backend, worker, and frontend with
hot reload. Production-ready images are published to GitHub Container Registry by `.github/workflows/release.yml` with semantic
version and SHA tags.

## Deployment

Releases publish `ghcr.io/<owner>/<repo>` containing the entire stack. Provide Temporal connectivity (e.g.,
`TEMPORAL_HOST=temporal-frontend.temporal.svc.cluster.local:7233`) and any secrets such as `OPENAI_API_KEY`. The container exposes
port `8124`; the frontend is available at `/`, while API consumers should target `http://<host>:8124/api`.

## Continuous Integration

`.github/workflows/ci.yml` runs targeted pipelines:

- Backend lint, type-check, and pytest when `apps/backend` or shared contracts change.
- Frontend lint, type-check, test, and build when `apps/frontend` or shared contracts change.

`.github/workflows/openapi.yml` regenerates and commits the shared OpenAPI schema on demand or after backend changes. Releases on
`main` invoke `.github/workflows/release.yml` which runs all quality gates, performs semantic-release, and publishes backend +
frontend container images to GHCR with semantic and SHA tags.

## Developer Tooling

- `.mise.toml` aggregates task shortcuts and tool versions (Python, uv, Bun, Node) so you can opt into runtime management without
  manual setup.
- Per-app `.mise.toml` files provide focused tasks (`mise run frontend.dev`, `mise run backend.worker`, etc.).

## Contributing

Follow Conventional Commits. Ensure tests and linters pass (`mise run backend.test frontend.test backend.lint frontend.lint`) before
opening a PR. Changes to backend endpoints should regenerate the OpenAPI schema and TypeScript bindings.
