"""Shared helpers for normalising resume ingestion structures."""
from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import asdict, is_dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    from .ingestion import ParsedExperience


def dedupe_skills(skills: Iterable[Any] | None) -> list[str]:
    """Return a stable list of unique skills preserving original order."""

    if not skills:
        return []
    if isinstance(skills, str):
        sequence: Iterable[Any] = [skills]
    else:
        sequence = skills
    deduped: list[str] = []
    seen: set[str] = set()
    for entry in sequence:
        if entry is None:
            continue
        if isinstance(entry, str):
            candidate = entry
        else:
            candidate = str(entry)
        cleaned = candidate.strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(cleaned)
    return deduped


def coerce_experiences(
    experiences: Sequence[Any] | Iterable[Any] | None,
    text: str,
) -> list["ParsedExperience"]:
    """Normalise heterogeneous experience payloads into dataclass instances."""

    from .ingestion import ParsedExperience  # Local import to avoid circular dependency

    if not experiences:
        entries: list[Any] = []
    elif isinstance(experiences, dict):
        entries = [experiences]
    else:
        entries = list(experiences)

    normalised: list[ParsedExperience] = []
    for entry in entries:
        parsed = _coerce_single_experience(entry)
        if parsed is None:
            continue
        achievements = [
            str(achievement).strip()
            for achievement in parsed.get("achievements", [])
            if str(achievement).strip()
        ]
        normalised.append(
            ParsedExperience(
                company=str(parsed.get("company") or "Experience"),
                role=str(parsed.get("role") or "Professional"),
                achievements=achievements,
                start_date=parsed.get("start_date"),
                end_date=parsed.get("end_date"),
                location=parsed.get("location"),
            )
        )

    if normalised:
        return normalised

    summary = " ".join(line.strip() for line in text.splitlines() if line.strip())
    achievements = [summary[:240]] if summary else []
    return [
        ParsedExperience(
            company="Uploaded Resume",
            role="Professional",
            achievements=achievements,
        )
    ]


def _coerce_single_experience(entry: Any) -> dict[str, Any] | None:
    """Return a dictionary representation of an experience entry."""

    if entry is None:
        return None
    if isinstance(entry, dict):
        return dict(entry)
    if is_dataclass(entry) and not isinstance(entry, type):
        return asdict(entry)
    model_dump = getattr(entry, "model_dump", None)
    if callable(model_dump):
        try:
            data = model_dump()
        except TypeError:  # pragma: no cover - defensive for unexpected signatures
            return None
        if isinstance(data, dict):
            return data
    # Fallback to attribute access for simple objects
    attributes = {}
    for field in ("company", "role", "achievements", "start_date", "end_date", "location"):
        if hasattr(entry, field):
            attributes[field] = getattr(entry, field)
    return attributes or None
