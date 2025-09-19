"""Semantic caching utilities for generated resumes."""

from __future__ import annotations

import asyncio
from difflib import SequenceMatcher

from app.config import get_settings
from app.core.cache import cache_get, cache_set
from app.core.security import fingerprint_job_posting
from app.models.resume import CachedResume


class SemanticCache:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._lock = asyncio.Lock()
        self._memory: dict[str, CachedResume] = {}

    async def get_similar(self, job_posting: str) -> CachedResume | None:
        job_hash = fingerprint_job_posting(job_posting)
        cached = await cache_get(job_hash)
        if cached is not None:
            resume = CachedResume.model_validate(cached)
            async with self._lock:
                self._memory[job_hash] = resume
            return resume

        async with self._lock:
            best: CachedResume | None = None
            best_score = 0.0
            for entry in self._memory.values():
                score = SequenceMatcher(None, entry.job_posting, job_posting).ratio()
                if score > best_score:
                    best_score = score
                    best = entry
            if best is None:
                return None
            if best_score >= self.settings.semantic_cache_similarity:
                return best
        return None

    async def store(self, job_posting: str, resume: dict, confidence: float = 1.0) -> CachedResume:
        job_hash = fingerprint_job_posting(job_posting)
        cached = CachedResume(
            job_hash=job_hash,
            job_posting=job_posting,
            resume=resume,
            confidence=confidence,
        )
        await cache_set(job_hash, cached.model_dump(mode="json"), ttl=self.settings.semantic_cache_ttl)
        async with self._lock:
            self._memory[job_hash] = cached
        return cached


__all__ = ["SemanticCache"]
