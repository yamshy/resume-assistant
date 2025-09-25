# Repository Guidelines

## Project Structure & Module Organization
The Svelte app lives in `src/`, with the entrypoint in `src/main.ts` and the root layout in `src/App.svelte`. Shared UI and logic modules belong under `src/lib/`, while static assets (icons, mock data) stay in `src/assets/` or `public/` so Vite can serve them directly. Global styles are centralized in `src/app.css`. Vitest test files should sit next to the code they cover using a `.test.ts` or `.spec.ts` suffix; shared test setup resides in `src/setupTests.ts`. Release automation now lives at the repository root (`.github/workflows/`).

## Build, Test, and Development Commands
Install dependencies with `mise run frontend.install` (or `bun install` directly). Use `mise run frontend.dev`/`bun run dev` for the Vite dev server with HMR, `mise run frontend.build` to emit the production bundle in `dist/`, and `bun run preview` to inspect the built output locally. Quality gates include `mise run frontend.lint`, `mise run frontend.test`, and `bun run check` (Svelte + TypeScript validation).

## Coding Style & Naming Conventions
Adopt Bun + Node >=18 locally. Follow the ESLint flat config (`eslint.config.js`) and Prettier defaults: two-space indentation, single quotes in TypeScript, and PascalCase for Svelte component filenames. Keep Svelte components lean by extracting reusable logic into `src/lib/` modules. Prefer semantic HTML, Tailwind-like utility classes, and TypeScript types or interfaces instead of `any`.

## Testing Guidelines
Vitest and Testing Library power the suite. New tests belong adjacent to features and should describe behavior (e.g., `resume-uploader.test.ts`). Leverage the helpers loaded via `src/setupTests.ts` for DOM assertions. Run `bun run test` before every PR; add focused specs when fixing bugs and capture edge cases such as empty responses or network errors.

## Commit & Pull Request Guidelines
Commits and PR titles must follow Conventional Commits (e.g., `feat: add resume upload button`, `fix(chat): prevent stale suggestions)`). Group related changes per commit, include a `BREAKING CHANGE` footer when needed, and avoid WIP prefixes. PRs should summarize intent, link tracking issues, list validation commands (`lint`, `check`, `test`), and attach UI screenshots or recordings when altering the interface.

## Release & Environment Notes
`semantic-release` drives versioning and publishes the Caddy-based container image directly from the GitHub Actions release workflow. Ensure main stays releasable: only merge after CI passes and the production build works locally with `bun run build`.
