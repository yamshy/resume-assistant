#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-8124}"

cleanup() {
  if [[ -n "${API_PID:-}" ]]; then
    kill "$API_PID" >/dev/null 2>&1 || true
  fi
  if [[ -n "${WORKER_PID:-}" ]]; then
    kill "$WORKER_PID" >/dev/null 2>&1 || true
  fi
}

trap cleanup INT TERM

uvicorn app.api:app --host 0.0.0.0 --port "$PORT" &
API_PID=$!

python worker.py &
WORKER_PID=$!

wait -n "$API_PID" "$WORKER_PID"
