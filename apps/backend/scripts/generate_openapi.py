"""Utility to export the FastAPI OpenAPI schema to disk."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from fastapi.encoders import jsonable_encoder

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MONOREPO_ROOT = PROJECT_ROOT.parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.api import app  # noqa: E402


def export_openapi_schema(output_path: Path) -> None:
    """Generate the OpenAPI schema for the FastAPI app and persist it."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    schema = app.openapi()
    encoded_schema = jsonable_encoder(schema)
    output_path.write_text(json.dumps(encoded_schema, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the OpenAPI schema file")
    default_output = MONOREPO_ROOT / "shared" / "api-types" / "openapi.json"
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=default_output,
        help=f"Path to write the generated schema to (default: {default_output})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    export_openapi_schema(args.output)


if __name__ == "__main__":
    main()
