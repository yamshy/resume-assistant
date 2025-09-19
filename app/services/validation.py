"""Human review workflows and validation helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
from uuid import UUID

from app.config import get_settings
from app.models.review import ReviewDecision, ReviewItem
from app.services.repository import ReviewRepository


@dataclass
class ConfidenceRules:
    base_threshold: float
    adjustment: float = 0.0

    @property
    def threshold(self) -> float:
        return max(0.3, min(0.95, self.base_threshold + self.adjustment))

    def apply_feedback(self, action: str) -> None:
        if action == "approve":
            self.adjustment = min(self.adjustment + 0.02, 0.2)
        elif action == "reject":
            self.adjustment = max(self.adjustment - 0.05, -0.2)
        elif action == "edit":
            self.adjustment = max(self.adjustment - 0.02, -0.2)


class ReviewService:
    def __init__(self, repository: ReviewRepository) -> None:
        self.repository = repository
        settings = get_settings()
        self.rules = ConfidenceRules(base_threshold=settings.review_confidence_threshold)

    async def store_pending_items(self, user_id: str, items: Iterable[ReviewItem]) -> None:
        items_list = list(items)
        if not items_list:
            return
        await self.repository.store_items(user_id, items_list)

    async def get_pending(self, user_id: str) -> list[ReviewItem]:
        return await self.repository.get_pending(user_id)

    async def approve(self, item_id: UUID) -> None:
        await self.repository.update_status(item_id, "approved")

    async def edit(self, item_id: UUID, new_content: str | None) -> None:
        await self.repository.update_status(item_id, "edited", new_content=new_content)

    async def reject(self, item_id: UUID) -> None:
        await self.repository.update_status(item_id, "rejected")

    async def process_decisions(self, user_id: str, decisions: list[ReviewDecision]) -> None:
        for decision in decisions:
            if decision.action == "approve":
                await self.approve(decision.item_id)
            elif decision.action == "edit":
                await self.edit(decision.item_id, decision.new_content)
            elif decision.action == "reject":
                await self.reject(decision.item_id)
        await self.update_confidence_rules(decisions)

    async def update_confidence_rules(self, decisions: Iterable[ReviewDecision]) -> None:
        for decision in decisions:
            self.rules.apply_feedback(decision.action)

    def current_threshold(self) -> float:
        return self.rules.threshold


__all__ = ["ReviewService", "ConfidenceRules"]
