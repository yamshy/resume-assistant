from __future__ import annotations

from pathlib import Path

import pytest

from resume_core.services.storage_service import StorageService


@pytest.mark.asyncio
async def test_storage_service_rejects_path_traversal(tmp_path: Path) -> None:
    storage_dir = tmp_path / "storage"
    storage = StorageService(storage_dir)

    with pytest.raises(ValueError):
        await storage.read_json("../outside.json")

    with pytest.raises(ValueError):
        await storage.write_text("../outside.txt", "forbidden")
