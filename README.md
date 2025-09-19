# Resume Tailoring API

Production-ready FastAPI service for ingesting resumes, building verified profiles, and
generating tailored resumes with human-in-the-loop verification.

## Features

- **Resume ingestion**: Parse PDF, DOCX, or text resumes into a consolidated master profile.
- **Deduplication and validation**: Merge overlapping experiences and tag low-confidence items for review.
- **Tailored generation**: Produce resumes aligned to job postings using only verified data.
- **Semantic cache**: Reuse previous generations for similar job descriptions to cut inference costs.
- **Human verification**: Workflow for approving, editing, or rejecting low-confidence claims.
- **Async-first architecture**: All pipelines run asynchronously with Redis caching and PostgreSQL (SQLite fallback for tests).
- **Observability**: Prometheus metrics and structured logging via `structlog`.

## Quickstart

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv)

### Setup

```bash
uv sync --frozen --all-extras
cp .env.example .env
```

### Local Development

```bash
# Run API with hot reload
uv run uvicorn app.main:app --reload

# Execute tests
uv run pytest

# Run code quality checks
uv run ruff check
uv run mypy app

# Smoke test the pipeline with dummy data
uv run python -m scripts.demo_pipeline
```

### Docker

```bash
cd docker
docker compose up --build
```

### Key Environment Variables

See `.env.example` for the full list. Important variables include:

- `DATABASE_URL` – Async SQLAlchemy connection string (Postgres in production).
- `REDIS_URL` – Redis connection URL or `memory://` for tests.
- `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` – Optional API keys for advanced generation.
- `SECRET_KEY` – Secret used for signing tokens.

## Testing Strategy

- Unit tests cover parsing, validation, and service logic.
- Integration tests exercise the full API flow end-to-end.
- GitHub Actions workflow runs linting, type checking, pytest with coverage, and security scanning.

## Project Structure

```
app/
├── api/           # FastAPI routers and dependencies
├── agents/        # Parsing, deduplication, generation, validation agents
├── config.py      # Pydantic settings
├── core/          # Database, cache, and security helpers
├── models/        # Pydantic schemas and ORM models
├── prompts/       # Prompt templates for LLM integrations
└── services/      # Application services and repositories
```

## Production Checklist

- Configure environment variables and secrets securely
- Run Alembic migrations against production database
- Enable HTTPS and proper CORS configuration
- Configure monitoring (Prometheus/Grafana) and alerting
- Set up log aggregation and backup strategy
- Review rate-limiting, authentication, and tracing requirements
