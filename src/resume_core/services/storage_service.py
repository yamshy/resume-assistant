from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID


class StorageService:
    def __init__(self, base_path: Path | str | None = None) -> None:
        resolved_base = Path(
            base_path or os.getenv("RESUME_ASSISTANT_DATA_DIR") or Path.home() / ".resume_assistant"
        )
        self.base_path = resolved_base
        self.resumes_path = self.base_path / "resumes"
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.resumes_path.mkdir(parents=True, exist_ok=True)
        self.base_path = self.base_path.resolve()
        self.resumes_path = self.resumes_path.resolve()

    @property
    def profile_path(self) -> Path:
        return self.base_path / "profile.json"

    def load_profile(self) -> dict[str, Any]:
        if not self.profile_path.exists():
            return {}
        return json.loads(self.profile_path.read_text())

    def save_profile(self, data: dict[str, Any]) -> None:
        self.profile_path.write_text(json.dumps(data, indent=2, sort_keys=True))

    def save_resume_snapshot(self, resume_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        record = self.load_resume(resume_id) if self.has_resume(resume_id) else {}
        history = record.get("history", [])
        payload.setdefault("history", history)
        self._write_resume(resume_id, payload)
        return payload

    def has_resume(self, resume_id: str) -> bool:
        try:
            path = self._resolve_resume_path(resume_id)
        except ValueError:
            return False
        return path.exists()

    def load_resume(self, resume_id: str) -> dict[str, Any]:
        path = self._resolve_resume_path(resume_id)
        if not path.exists():
            raise FileNotFoundError(f"Resume {resume_id} not found")
        return json.loads(path.read_text())

    def update_resume(self, resume_id: str, update: dict[str, Any]) -> dict[str, Any]:
        record = self.load_resume(resume_id)
        record.update(update)
        self._write_resume(resume_id, record)
        return record

    def list_resume_metadata(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for path in sorted(self.resumes_path.glob("*.json")):
            data = json.loads(path.read_text())
            resume = data.get("resume", {})
            items.append(
                {
                    "resume_id": resume.get("resume_id", path.stem),
                    "status": data.get("status", "draft"),
                    "job_title": resume.get("job_title"),
                    "created_at": resume.get("created_at"),
                }
            )
        return items

    def _write_resume(self, resume_id: str, payload: dict[str, Any]) -> None:
        self.resumes_path.mkdir(parents=True, exist_ok=True)
        path = self._resolve_resume_path(resume_id)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=self._json_default))

    @staticmethod
    def _json_default(value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    def _resolve_resume_path(self, resume_id: str) -> Path:
        normalized_id = self._normalize_resume_id(resume_id)
        path = (self.resumes_path / f"{normalized_id}.json").resolve()
        if not path.is_relative_to(self.resumes_path):
            raise ValueError("Invalid resume identifier")
        return path

    @staticmethod
    def _normalize_resume_id(resume_id: str) -> str:
        try:
            return str(UUID(resume_id))
        except ValueError as exc:  # pragma: no cover - validation path
            raise ValueError("Invalid resume identifier") from exc
