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
COPY main.py ./
COPY worker.py ./

ARG TARGET=api
ENV TARGET_SERVICE=${TARGET}

EXPOSE 8080

CMD ["sh", "-c", "if [ \"$TARGET_SERVICE\" = \"worker\" ]; then python worker.py; else uvicorn app.api:app --host 0.0.0.0 --port 8080; fi"]
