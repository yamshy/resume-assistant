"""Resume orchestrator that relies on AI for reasoning and planning."""

from __future__ import annotations

import json
import os
from hashlib import sha256
from textwrap import dedent
from typing import Any

from openai import AsyncOpenAI

from app.storage import MemoryStorage


class ResumeOrchestrator:
    """Coordinates resume generation while delegating reasoning to the model."""

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

    async def generate_with_memory(
        self,
        job_posting: str,
        profile: dict[str, Any],
        discovered: dict[str, Any],
        preferences: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a tailored resume leveraging stored knowledge."""

        cache_key = self._cache_key(job_posting, profile, discovered, preferences)
        cached = self.storage.load_cached_resume(cache_key)
        if cached:
            cached["status"] = "cached"
            cached.setdefault("cache_key", cache_key)
            return cached

        system_message = dedent(
            """
            You are an expert resume strategist. You always:
            - use ONLY verified profile data or approved discoveries
            - respect the user's preferences and corrections
            - provide confidence scores for every major section
            - flag anything uncertain for human review
            Respond strictly as JSON.
            """
        ).strip()

        payload = {
            "job_posting": job_posting,
            "verified_profile": profile,
            "discovered_items": discovered,
            "preferences": preferences,
        }
        user_message = dedent(
            """
            Tailor a resume for the provided job posting.

            Requirements:
            1. Consider verified profile data and the discovered-but-unapproved items.
            2. Do not fabricate experience or skills.
            3. Respect stylistic preferences when suggesting language.
            4. Provide confidence scores (0.0-1.0) for each resume section.
            5. List items that should go to human review when confidence < 0.8.

            Return JSON with the following keys:
            - "resume_text": formatted resume text ready for presentation.
            - "sections": mapping of section name to bullet points or details.
            - "confidence": overall confidence score between 0 and 1.
            - "section_confidence": mapping of section name to scores.
            - "review_flags": list of items needing human approval.
            - "conversation": short reasoning trace so the memory agent can learn.
            - "used_discoveries": list of discovery identifiers that were referenced.
            - "cache_key": repeat the cache identifier you used.
            """
        ).strip()
        payload["cache_key"] = cache_key

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        data.setdefault("status", "generated")
        data.setdefault("cache_key", cache_key)
        if "conversation" not in data:
            data["conversation"] = user_message

        self.storage.store_cached_resume(cache_key, data)
        return data

    def _cache_key(
        self,
        job_posting: str,
        profile: dict[str, Any],
        discovered: dict[str, Any],
        preferences: dict[str, Any],
    ) -> str:
        """Build a deterministic cache key from key inputs."""

        parts = json.dumps(
            {
                "job_posting": job_posting,
                "profile_version": profile.get("last_updated"),
                "experiences": [exp.get("id") for exp in profile.get("experiences", [])],
                "discovered": discovered,
                "preferences": preferences,
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        return sha256(parts.encode("utf-8")).hexdigest()


__all__ = ["ResumeOrchestrator"]
