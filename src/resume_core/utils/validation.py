from __future__ import annotations

from typing import Final

VALID_DECISIONS: Final[dict[str, str]] = {
    "approve": "approved",
    "approved": "approved",
    "accept": "approved",
    "changes_requested": "changes_requested",
    "request_changes": "changes_requested",
    "revise": "changes_requested",
    "reject": "rejected",
    "rejected": "rejected",
}


def ensure_decision_value(decision: str) -> str:
    normalized = decision.strip().lower()
    if normalized not in VALID_DECISIONS:
        raise ValueError(f"Unsupported decision value: {decision}")
    return VALID_DECISIONS[normalized]
