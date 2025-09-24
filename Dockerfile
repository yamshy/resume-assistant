# syntax=docker/dockerfile:1
FROM python:3.13-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "uv>=0.4,<0.5"

COPY pyproject.toml uv.lock ./
RUN uv pip install --system --no-build-isolation -r pyproject.toml

COPY app ./app
COPY langgraph.json ./
COPY main.py ./
COPY README.md ./

EXPOSE 8030

ENV LANGGRAPH_CONFIG=/app/langgraph.json

CMD [
  "langgraph",
  "server",
  "start",
  "--config",
  "/app/langgraph.json",
  "--host",
  "0.0.0.0",
  "--port",
  "8030"
]
