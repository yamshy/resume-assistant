"""File-backed storage with memory for the resume service."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml


class MemoryStorage:
    """Persists profile data, discovered items, and cache entries on disk."""

    def __init__(self, data_dir: str | Path = "./data") -> None:
        self.data_dir = Path(data_dir)
        self.memory_dir = self.data_dir / "memory"
        self.cache_dir = self.data_dir / "cache"
        self.profile_file = self.data_dir / "profile.yaml"
        self.discovered_file = self.memory_dir / "discovered.yaml"
        self.preferences_file = self.memory_dir / "preferences.yaml"
        self.corrections_file = self.memory_dir / "corrections.yaml"
        self.pending_review_file = self.data_dir / "pending_review.json"
        self.learning_file = self.data_dir / "learning.yaml"

        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self._ensure_defaults()

    # ------------------------------------------------------------------
    # Memory helpers
    # ------------------------------------------------------------------
    def remember_skill(self, skill: dict[str, Any], context: str) -> dict[str, Any]:
        """Store a newly discovered skill."""

        memory = self._load_yaml(self.discovered_file, default={"discovered_skills": []})
        entry = {**skill}
        entry.setdefault("id", self._make_identifier("skill", entry.get("name")))
        entry["discovered_date"] = self._timestamp()
        entry.setdefault("discovered_from", context)
        entry.setdefault("confidence", skill.get("confidence", 0.8))
        entry.setdefault("added_to_profile", False)
        memory.setdefault("discovered_skills", []).append(entry)
        self._save_yaml(self.discovered_file, memory)
        return entry

    def remember_experience(self, experience: dict[str, Any], context: str) -> dict[str, Any]:
        """Store a newly discovered experience awaiting approval."""

        memory = self._load_yaml(self.discovered_file, default={})
        entry = {**experience}
        entry.setdefault("id", self._make_identifier("experience", experience.get("context")))
        entry.setdefault("status", "pending_approval")
        entry["discovered_date"] = self._timestamp()
        entry.setdefault("discovered_from", context)
        memory.setdefault("discovered_experiences", []).append(entry)
        self._save_yaml(self.discovered_file, memory)
        return entry

    def remember_achievement(self, achievement: dict[str, Any], context: str) -> dict[str, Any]:
        """Store a discovered achievement or impact statement."""

        memory = self._load_yaml(self.discovered_file, default={})
        entry = {**achievement}
        entry.setdefault("id", self._make_identifier("achievement", achievement.get("achievement")))
        entry["discovered_date"] = self._timestamp()
        entry.setdefault("discovered_from", context)
        entry.setdefault("added_to_profile", False)
        memory.setdefault("discovered_achievements", []).append(entry)
        self._save_yaml(self.discovered_file, memory)
        return entry

    def remember_preference(self, category: str, preference: dict[str, Any]) -> dict[str, Any]:
        """Persist user preferences for future generations."""

        prefs = self._load_yaml(self.preferences_file, default={})
        prefs.setdefault(category, [])
        entry = {**preference}
        entry.setdefault("learned_date", self._timestamp())
        prefs[category].append(entry)
        self._save_yaml(self.preferences_file, prefs)
        return entry

    def remember_correction(self, original: str, corrected: str, context: str) -> dict[str, Any]:
        """Track corrections to automatically apply them later."""

        corrections = self._load_yaml(self.corrections_file, default={"corrections": []})
        existing = next(
            (item for item in corrections.get("corrections", []) if item.get("original") == original),
            None,
        )
        if existing:
            existing["corrected_to"] = corrected
            existing["context"] = context
            existing["times_applied"] = int(existing.get("times_applied", 1)) + 1
            existing.setdefault("learned_date", self._timestamp())
            entry = existing
        else:
            entry = {
                "original": original,
                "corrected_to": corrected,
                "context": context,
                "learned_date": self._timestamp(),
                "times_applied": 1,
            }
            corrections.setdefault("corrections", []).append(entry)
        self._save_yaml(self.corrections_file, corrections)
        return entry

    def record_learning_pattern(self, entry: dict[str, Any]) -> None:
        """Append a learning pattern for analytics or future improvements."""

        data = self._load_yaml(self.learning_file, default={"patterns": []})
        entry = {**entry, "recorded_at": self._timestamp()}
        data.setdefault("patterns", []).append(entry)
        self._save_yaml(self.learning_file, data)

    def get_discovered_items(self) -> dict[str, Any]:
        """Return discoveries that still require approval."""

        discovered = self._load_yaml(
            self.discovered_file,
            default={"discovered_skills": [], "discovered_experiences": [], "discovered_achievements": []},
        )
        return {
            "skills": [item for item in discovered.get("discovered_skills", []) if not item.get("added_to_profile")],
            "experiences": [
                item
                for item in discovered.get("discovered_experiences", [])
                if item.get("status") in {"pending", "pending_approval", None} or not item.get("status")
            ],
            "achievements": [
                item
                for item in discovered.get("discovered_achievements", [])
                if not item.get("added_to_profile")
            ],
        }

    def promote_to_profile(self, item_type: str, item_id: str) -> None:
        """Move an approved discovery into the main profile."""

        discovered = self._load_yaml(self.discovered_file, default={})
        profile = self.load_profile()

        if item_type == "skill":
            skill = self._find_by_id(discovered.get("discovered_skills", []), item_id)
            if not skill:
                raise ValueError(f"Unknown skill id: {item_id}")
            skill["added_to_profile"] = True
            profile.setdefault("skills", {}).setdefault("technical", []).append(
                {
                    "name": skill.get("name"),
                    "source": "discovered",
                    "added_date": self._timestamp(),
                    "confidence": skill.get("confidence", 0.8),
                }
            )
        elif item_type == "experience":
            experience = self._find_by_id(discovered.get("discovered_experiences", []), item_id)
            if not experience:
                raise ValueError(f"Unknown experience id: {item_id}")
            experience["status"] = "approved"
            profile.setdefault("experiences", []).append(
                {**experience, "source": "discovered", "added_date": self._timestamp()}
            )
        elif item_type == "achievement":
            achievement = self._find_by_id(discovered.get("discovered_achievements", []), item_id)
            if not achievement:
                raise ValueError(f"Unknown achievement id: {item_id}")
            achievement["added_to_profile"] = True
            self.record_learning_pattern(
                {
                    "type": "achievement",
                    "details": achievement.get("achievement"),
                    "related_to": achievement.get("related_to"),
                }
            )
        else:
            raise ValueError(f"Unsupported item type: {item_type}")

        self.save_profile(profile)
        self._save_yaml(self.discovered_file, discovered)

    def get_preferences(self) -> dict[str, Any]:
        return self._load_yaml(self.preferences_file, default={})

    def get_corrections(self) -> list[dict[str, Any]]:
        corrections = self._load_yaml(self.corrections_file, default={"corrections": []})
        return corrections.get("corrections", [])

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------
    def store_cached_resume(self, cache_key: str, payload: dict[str, Any]) -> None:
        path = self.cache_dir / f"{cache_key}.json"
        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)

    def load_cached_resume(self, cache_key: str) -> dict[str, Any] | None:
        path = self.cache_dir / f"{cache_key}.json"
        if not path.exists():
            return None
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def clear_cache(self) -> None:
        for file in self.cache_dir.glob("*.json"):
            file.unlink(missing_ok=True)

    # ------------------------------------------------------------------
    # Profile helpers
    # ------------------------------------------------------------------
    def load_profile(self) -> dict[str, Any]:
        return self._load_yaml(
            self.profile_file,
            default={"version": "1.0", "last_updated": self._timestamp(), "experiences": [], "skills": {}},
        )

    def save_profile(self, profile: dict[str, Any]) -> None:
        profile = {**profile, "last_updated": self._timestamp()}
        self._save_yaml(self.profile_file, profile)

    # ------------------------------------------------------------------
    # Private utilities
    # ------------------------------------------------------------------
    def _ensure_defaults(self) -> None:
        if not self.profile_file.exists():
            self.save_profile({"version": "1.0", "experiences": [], "skills": {}})
        if not self.discovered_file.exists():
            self._save_yaml(
                self.discovered_file,
                {"discovered_skills": [], "discovered_experiences": [], "discovered_achievements": []},
            )
        if not self.preferences_file.exists():
            self._save_yaml(self.preferences_file, {})
        if not self.corrections_file.exists():
            self._save_yaml(self.corrections_file, {"corrections": []})
        if not self.pending_review_file.exists():
            self.pending_review_file.write_text("[]", encoding="utf-8")
        if not self.learning_file.exists():
            self._save_yaml(self.learning_file, {"patterns": []})

    def _load_yaml(self, path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
                if isinstance(data, dict):
                    return data
                return default or {}
        return default or {}

    def _save_yaml(self, path: Path, data: dict[str, Any]) -> None:
        with path.open("w", encoding="utf-8") as handle:
            yaml.dump(data, handle, sort_keys=False, allow_unicode=True)

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()  # noqa: UP017

    def _make_identifier(self, prefix: str, seed: str | None) -> str:
        base = seed or uuid4().hex[:8]
        slug = sha256(base.encode("utf-8")).hexdigest()[:12]
        return f"{prefix}_{slug}"

    def _find_by_id(self, items: list[dict[str, Any]], item_id: str) -> dict[str, Any] | None:
        for item in items:
            if item.get("id") == item_id:
                return item
        return None

__all__ = ["MemoryStorage"]
