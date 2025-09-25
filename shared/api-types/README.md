# Shared API Types

This directory stores generated API schemas and client types shared between the FastAPI backend and the Svelte frontend.

## Regenerate the OpenAPI schema

```bash
mise run export-openapi
```

The command regenerates `openapi.json` using the live FastAPI app configuration.

## Generate frontend TypeScript bindings

Run the frontend type generation script (requires `openapi-typescript` in the frontend dev dependencies):

```bash
mise run gen-types
```

Generated types live in `apps/frontend/src/lib/api/types.ts`. Commit both the schema and generated types to keep the contract in sync.
