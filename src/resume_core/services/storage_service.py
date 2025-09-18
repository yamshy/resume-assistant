from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any


class StorageService:
    def __init__(self, base_path: Path) -> None:
        self.base_path = Path(base_path).resolve()
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve(self, relative: str | Path) -> Path:
        candidate = Path(relative)
        if candidate.is_absolute():
            raise ValueError("absolute paths are not allowed")
        resolved = (self.base_path / candidate).resolve()
        if not resolved.is_relative_to(self.base_path):
            raise ValueError("attempted path traversal outside storage root")
        return resolved

    async def read_json(self, relative: str | Path) -> dict[str, Any] | None:
        path = self._resolve(relative)
        if not path.exists():
            return None
        data = await asyncio.to_thread(path.read_text)
        return json.loads(data)

    async def write_json(self, relative: str | Path, data: dict[str, Any]) -> None:
        path = self._resolve(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(data, indent=2)
        await asyncio.to_thread(path.write_text, content)

    async def read_text(self, relative: str | Path) -> str | None:
        path = self._resolve(relative)
        if not path.exists():
            return None
        return await asyncio.to_thread(path.read_text)

    async def write_text(self, relative: str | Path, content: str) -> None:
        path = self._resolve(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_text, content)

    async def list_files(self, relative: str | Path) -> list[Path]:
        path = self._resolve(relative)
        if not path.exists():
            return []
        return [item for item in path.iterdir() if item.is_file()]
