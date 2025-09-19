"""Agent responsible for learning and applying personal preferences."""

from __future__ import annotations

import json
import os
from typing import Any

from openai import AsyncOpenAI

from app.storage import MemoryStorage


class MemoryAgent:
    """Analyzes conversations to grow long-term memory."""

    def __init__(
        self,
        *,
        storage: MemoryStorage | None = None,
        client: AsyncOpenAI | None = None,
        model: str | None = None,
    ) -> None:
        api_key = os.getenv("OPENAI_API_KEY", "test-key")
        self.client = client or AsyncOpenAI(api_key=api_key)
        self.model = model or os.getenv("MODEL_NAME", "gpt-4o-mini")
        self.storage = storage or MemoryStorage()

    async def analyze_conversation(
        self, conversation: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Identify new skills, experiences, and preferences from dialogue."""

        prompt = {
            "conversation": conversation,
            "profile_summary": context,
            "instructions": [
                "List new skills or experiences not in the profile.",
                "Extract user preferences about tone, emphasis, or formatting.",
                "Capture corrections the user made repeatedly.",
                "Note any extra context about existing experiences.",
                "Return JSON so the system can store the discoveries.",
            ],
        }

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You analyze resume conversations to learn about the user.",
                },
                {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        discoveries = json.loads(content)

        for skill in discoveries.get("new_skills", []) or []:
            self.storage.remember_skill(skill, conversation[:100])

        for experience in discoveries.get("new_experiences", []) or []:
            self.storage.remember_experience(experience, conversation[:120])

        for achievement in discoveries.get("achievements", []) or []:
            self.storage.remember_achievement(achievement, conversation[:120])

        preferences = discoveries.get("preferences", {}) or {}
        for category, pref_value in preferences.items():
            if isinstance(pref_value, dict):
                self.storage.remember_preference(category, pref_value)

        for correction in discoveries.get("corrections", []) or []:
            original = correction.get("original")
            edited = correction.get("corrected_to") or correction.get("edited")
            if original and edited:
                self.storage.remember_correction(
                    original,
                    edited,
                    correction.get("context", "Conversation analysis"),
                )

        additional = discoveries.get("additional_context")
        if additional:
            self.storage.record_learning_pattern({"type": "context", "details": additional})

        return discoveries

    async def apply_learned_preferences(self, content: str) -> str:
        """Ask the LLM to apply stored preferences to generated content."""

        preferences = self.storage.get_preferences()
        corrections = self.storage.get_corrections()
        payload = {
            "content": content,
            "preferences": preferences,
            "corrections": corrections,
        }
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Rewrite text using the user's preferences and corrections.",
                },
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
        )
        return response.choices[0].message.content or content

    async def learn_from_decision(self, decision: dict[str, Any]) -> dict[str, Any]:
        """Update memory based on explicit human review decisions."""

        payload = {
            "decision": decision,
            "instructions": [
                "Determine if this decision reveals a new skill or achievement.",
                "Identify preference adjustments implied by the edit.",
                "Return JSON with optional keys new_skill, new_preference, notes.",
            ],
        }
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You learn from resume review decisions."},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "{}"
        learning = json.loads(content)

        new_skill = learning.get("new_skill")
        if new_skill:
            self.storage.remember_skill(
                new_skill, f"Review decision {decision.get('id', 'unknown')}"
            )
            learning["new_skill_discovered"] = True
        else:
            learning["new_skill_discovered"] = False

        preference = learning.get("new_preference")
        if preference and isinstance(preference, dict):
            for category, value in preference.items():
                self.storage.remember_preference(category, value)

        note = learning.get("notes")
        if note:
            self.storage.record_learning_pattern({"type": "review_note", "details": note})

        return learning


__all__ = ["MemoryAgent"]
