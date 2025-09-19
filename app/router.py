"""Model routing for cost optimised generation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class RoutingRule:
    model: str
    keywords: tuple[str, ...]
    cost_per_1k: float


class ModelRouter:
    """Select the cheapest capable model based on role seniority."""

    ROUTING_RULES: Dict[str, RoutingRule] = {
        "entry_level": RoutingRule(
            model="gpt-4o-mini",
            keywords=("junior", "entry", "graduate", "intern"),
            cost_per_1k=0.00015,
        ),
        "standard": RoutingRule(
            model="gpt-4o-mini",
            keywords=("developer", "engineer", "analyst", "consultant"),
            cost_per_1k=0.00015,
        ),
        "senior": RoutingRule(
            model="gpt-4o",
            keywords=("senior", "lead", "principal", "staff"),
            cost_per_1k=0.0025,
        ),
        "executive": RoutingRule(
            model="gpt-4o",
            keywords=("director", "vp", "chief", "cto", "ceo", "cfo"),
            cost_per_1k=0.0025,
        ),
    }

    def select_model(self, job_posting: str, profile: dict) -> str:
        posting = job_posting.lower()
        years = self._extract_years(profile)

        if years <= 2:
            return self.ROUTING_RULES["entry_level"].model

        if years >= 12 and any(keyword in posting for keyword in self.ROUTING_RULES["executive"].keywords):
            return self.ROUTING_RULES["executive"].model

        if years >= 7 and any(keyword in posting for keyword in self.ROUTING_RULES["senior"].keywords):
            return self.ROUTING_RULES["senior"].model

        if any(keyword in posting for keyword in self.ROUTING_RULES["standard"].keywords):
            return self.ROUTING_RULES["standard"].model

        return self.ROUTING_RULES["entry_level"].model

    def _extract_years(self, profile: dict) -> int:
        years = profile.get("years_experience")
        if isinstance(years, (int, float)):
            return int(years)

        experiences = profile.get("experience") or profile.get("experiences")
        total = 0.0
        if isinstance(experiences, list):
            for entry in experiences:
                if not isinstance(entry, dict):
                    continue
                entry_years = entry.get("years")
                if isinstance(entry_years, (int, float)):
                    total += float(entry_years)
                    continue
                # fallback to parse text
                description = " ".join(str(value) for value in entry.values())
                total += self._years_from_text(description)
        return int(total) if total else 0

    @staticmethod
    def _years_from_text(text: str) -> float:
        matches = re.findall(r"(\d+(?:\.\d+)?)\s*(?:\+\s*)?(?:years|yrs)", text, flags=re.I)
        return sum(float(match) for match in matches)
