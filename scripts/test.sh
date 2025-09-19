#!/usr/bin/env bash
set -euo pipefail

uv run pytest --cov=app --cov-report=term-missing "$@"
