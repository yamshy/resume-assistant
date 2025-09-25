# Resume Assistant UI

A Svelte + Vite frontend that provides the user interface for the Resume Assistant experience. This project now includes a fully
scripted test suite, automated CI/CD workflows, and container image releases published to GitHub Container Registry (GHCR) using
semantic version numbers derived from Conventional Commits.

## Prerequisites

- [Bun](https://bun.sh/) `1.1.27` – used for dependency management and running the project locally. This version matches the
  runtime pinned in CI to avoid dependency resolution mismatches.
- [Node.js](https://nodejs.org/) `>=18` – required for some tooling, including Vitest.
- [Docker](https://www.docker.com/) – required only when building or publishing the production container image.

For an integrated backend + frontend + Temporal environment, run `mise run dev` from the repository root. This launches the
FastAPI backend, Temporal worker, and Bun dev server via Docker Compose.

> The repository contains a `bun.lock` file. Use `bun install` to ensure dependencies are resolved consistently with CI.

## Installation

```bash
bun install
```

## Available scripts

| Command | Description |
| ------- | ----------- |
| `bun run dev` | Starts the Vite development server with hot module reloading. |
| `bun run build` | Builds the production assets into `dist/`. |
| `bun run preview` | Serves the built production bundle locally. |
| `bun run lint` | Lints Svelte, TypeScript, and JavaScript sources with ESLint. |
| `bun run check` | Runs type-checking via `svelte-check` and `tsc`. |
| `bun run test` | Executes the Vitest suite once with coverage output. |
| `bun run test:watch` | Starts Vitest in watch mode for local development. |
| `bun run generate-types` | Regenerates API typings from `shared/api-types/openapi.json`. |

## Testing

The project uses [Vitest](https://vitest.dev/) together with Testing Library to validate critical chat utilities. Tests run in a
JSDOM environment so browser APIs (such as `File` and `crypto`) are available. To execute the suite locally, run:

```bash
bun run test
```

Coverage reports are written to the console and `coverage/` (LCOV) for inspection or integration with code-quality tooling.

## Continuous Integration

GitHub Actions in [`.github/workflows/ci.yml`](../../.github/workflows/ci.yml) run on every push and pull request. Changes inside
`apps/frontend` (or shared API contracts) trigger targeted jobs that install dependencies with Bun and run:

1. `bun run lint`
2. `bun run check`
3. `bun run test`
4. `bun run build`

Any failure in these steps will fail the workflow, helping to keep the main branch in a deployable state.

## Release Automation & GHCR Publishing

Releases are generated automatically from the Conventional Commit history using
[`semantic-release`](https://github.com/semantic-release/semantic-release). When changes land on the `main` branch, the
[`release.yml`](.github/workflows/release.yml) workflow (restricted to the `main` branch):

1. Runs the full CI test suite.
2. Invokes `semantic-release` to determine the next semantic version.
3. Builds both the backend and frontend Docker images (this UI uses [`Dockerfile`](Dockerfile)).
4. Publishes the UI image to GHCR as `ghcr.io/<owner>/<repo>-frontend:<version>` along with `latest`, semantic, and SHA tags.
5. Updates `CHANGELOG.md` and the `package.json` version, then creates a GitHub release with generated notes.

The workflow relies on the built-in `GITHUB_TOKEN` secret for pushing images to GHCR. Ensure the repository (or organization)
allows the token to write packages. If you need to run the release workflow locally, export a `GITHUB_TOKEN` or personal access
token with the `write:packages` scope and log into GHCR before executing `npx semantic-release`.

## Conventional Commits

Semantic versioning is inferred from commit messages. Follow the
[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification when contributing. Examples:

- `feat: add resume upload button`
- `fix(chat): handle empty assistant responses`
- `chore(ci): update release workflow`

Breaking changes must include an exclamation mark (e.g., `feat!: drop legacy API`) or a `BREAKING CHANGE:` footer to trigger a
major version bump.

## Container Image

The published container image serves the static build with [Caddy](https://caddyserver.com/). You can run it locally after a
release with:

```bash
docker run --rm -p 8080:80 ghcr.io/<owner>/<repo>:<tag>
```

Replace `<owner>`, `<repo>`, and `<tag>` with the appropriate repository owner, repository name, and version (or `latest`).

## License

This project inherits the license of the parent repository. Refer to the repository's root for licensing details.
