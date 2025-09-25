from __future__ import annotations

from typing import Iterable, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - typing-only import
    from ..tools import ToolRegistry

_REGISTRY: "ToolRegistry | None" = None


def configure_registry(registry: Optional["ToolRegistry"] = None) -> "ToolRegistry":
    """Set the registry used by activities and return it for convenience."""

    global _REGISTRY
    if registry is None:
        from ..tools import build_default_registry

        resolved = build_default_registry()
    else:
        resolved = registry
    _REGISTRY = resolved
    return resolved


def get_registry() -> "ToolRegistry":
    if _REGISTRY is None:  # pragma: no cover - defensive guard
        raise RuntimeError("Activity registry has not been configured")
    return _REGISTRY


def list_all_activities() -> List[object]:
    """Return every activity registered in this package."""

    from . import compliance, critique, drafting, ingestion, publishing

    activities: Iterable[object] = (
        compliance.run_compliance_check,
        critique.run_critique,
        drafting.plan_resume,
        drafting.render_resume,
        ingestion.index_documents,
        ingestion.normalize_documents,
        publishing.notify_operations,
        publishing.persist_resume,
    )
    return list(activities)


__all__ = [
    "configure_registry",
    "get_registry",
    "list_all_activities",
]
