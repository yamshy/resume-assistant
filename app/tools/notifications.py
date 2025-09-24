from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(slots=True)
class NotificationTool:
    """Collect operational notifications emitted by the publishing graph."""

    name: str = "notification_dispatch"
    description: str = "Accumulate notifications for downstream channels."
    _events: List[Dict[str, str]] = field(default_factory=list)

    def publish(self, payload: Dict[str, str]) -> Dict[str, str]:
        event = {"status": payload.get("status", "queued"), "recipient": payload.get("recipient", "operations"), "message": payload.get("message", "")}
        self._events.append(event)
        return event

    @property
    def events(self) -> List[Dict[str, str]]:
        return list(self._events)

    def clear(self) -> None:
        self._events.clear()


__all__ = ["NotificationTool"]
