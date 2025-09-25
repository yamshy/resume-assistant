# syntax=docker/dockerfile:1.7

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

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY app ./app
COPY main.py worker.py ./
RUN uv sync --frozen --no-dev

FROM base AS production

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app ./app
COPY --from=builder /app/main.py ./main.py
COPY --from=builder /app/worker.py ./worker.py

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8124

CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8124"]
