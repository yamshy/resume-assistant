"""Export the OpenAPI schema for the FastAPI application."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from fastapi.openapi.utils import get_openapi

from app import create_app


def export_schema(destination: Path) -> None:
    """Generate the OpenAPI schema and persist it to ``destination``."""
    app = create_app()
    schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )
    destination.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> None:
    export_schema(REPO_ROOT / "openapi.json")


if __name__ == "__main__":
    main()
