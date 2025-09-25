from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass(slots=True)
class PublishingCacheTool:
    """Idempotent cache for storing generated resumes by request id."""

    name: str = "publishing_cache"
    description: str = "Persist resume artifacts for reuse and auditing."
    _cache: Dict[str, Dict[str, str]] = field(default_factory=dict)

    def store(self, request_id: str, *, resume: str, checksum: str) -> Dict[str, str]:
        self._cache[request_id] = {"resume": resume, "checksum": checksum}
        return self._cache[request_id]

    def fetch(self, request_id: str) -> Optional[Dict[str, str]]:
        return self._cache.get(request_id)

    def clear(self) -> None:
        self._cache.clear()


__all__ = ["PublishingCacheTool"]
