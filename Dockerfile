# syntax=docker/dockerfile:1
FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system build deps required by some wheels
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Use uv for fast, cache-friendly dependency installation
RUN pip install --no-cache-dir "uv>=0.4,<0.5"

COPY pyproject.toml uv.lock ./
RUN uv pip install --system --frozen --no-build-isolation -r pyproject.toml

COPY app ./app
COPY main.py ./
COPY README.md ./

# Expose the default application port
EXPOSE 8000

# Persist knowledge store data under /data inside the container
ENV KNOWLEDGE_STORE_PATH=/data/knowledge_store.json

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
