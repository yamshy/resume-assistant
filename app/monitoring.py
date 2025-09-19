"""Observability helpers for resume generations."""

from __future__ import annotations

import logging
from typing import Optional

from langsmith import traceable

from .router import ModelRouter

logger = logging.getLogger(__name__)


class _NullStatsD:
    def gauge(self, *_, **__):
        pass

    def histogram(self, *_, **__):
        pass

    def increment(self, *_, **__):
        pass


try:  # pragma: no cover - optional dependency
    from datadog import statsd as datadog_statsd
except Exception:  # pragma: no cover - fallback for local runs
    datadog_statsd = _NullStatsD()


class ResumeMonitor:
    """Track generation cost and quality metrics."""

    def __init__(self, stats_client: Optional[object] = None) -> None:
        self.stats = stats_client or datadog_statsd

    @traceable(name="resume.generation")
    async def track_generation(
        self,
        model: str,
        tokens_used: int,
        generation_time: float,
        confidence: float,
        cache_hit: bool,
    ) -> None:
        cost = self._calculate_cost(model, tokens_used)
        self.stats.gauge("resume.generation.cost", cost)
        self.stats.histogram("resume.generation.latency", generation_time)
        self.stats.gauge("resume.confidence", confidence)
        metric = "resume.cache.hit" if cache_hit else "resume.cache.miss"
        self.stats.increment(metric)

        if confidence < 0.7:
            await self._alert_low_confidence(confidence)
        if cost > 0.1:
            await self._alert_high_cost(cost, model)

    async def _alert_low_confidence(self, confidence: float) -> None:
        logger.warning("Low resume confidence detected: %.2f", confidence)

    async def _alert_high_cost(self, cost: float, model: str) -> None:
        logger.warning("High resume generation cost %.4f for model %s", cost, model)

    def _calculate_cost(self, model: str, tokens_used: int) -> float:
        for rule in ModelRouter.ROUTING_RULES.values():
            if rule.model == model:
                return rule.cost_per_1k * (tokens_used / 1000)
        return 0.0
