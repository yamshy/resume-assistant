# syntax=docker/dockerfile:1.7

FROM oven/bun:1.1.27 AS frontend-builder
WORKDIR /frontend
COPY apps/frontend/package.json apps/frontend/bun.lock ./
RUN bun install --frozen-lockfile
COPY apps/frontend/ ./
RUN bun run build

FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

FROM base AS builder

# Install uv from the official static build image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY apps/backend/pyproject.toml apps/backend/uv.lock ./
RUN uv sync --frozen --no-install-project

COPY apps/backend/app ./app
COPY apps/backend/main.py apps/backend/worker.py ./
COPY apps/backend/scripts ./scripts
RUN uv sync --frozen --no-dev

RUN mkdir -p ./app/frontend/dist
COPY --from=frontend-builder /frontend/dist ./app/frontend/dist

FROM base AS production

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app ./app
COPY --from=builder /app/main.py ./main.py
COPY --from=builder /app/worker.py ./worker.py
COPY --from=builder /app/scripts ./scripts

RUN chmod +x /app/scripts/*.sh

ENV PATH="/app/.venv/bin:$PATH" \
    FRONTEND_DIST_DIR=/app/app/frontend/dist \
    PORT=8124

EXPOSE 8124

CMD ["/app/scripts/start.sh"]
