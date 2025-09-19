"""Semantic caching layer to avoid redundant generations."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional

from .embeddings import SemanticEmbedder
from .models import Resume
from .utils import cosine_similarity


class SemanticCache:
    """Cache resumes and reuse them when inputs are semantically similar."""

    def __init__(
        self,
        redis_client,
        embedder: Optional[SemanticEmbedder] = None,
        similarity_threshold: float = 0.92,
        ttl: timedelta = timedelta(days=7),
    ) -> None:
        self.redis = redis_client
        self.embedder = embedder or SemanticEmbedder()
        self.similarity_threshold = similarity_threshold
        self.ttl = int(ttl.total_seconds())

    async def get(self, job_posting: str, profile: dict) -> Optional[Resume]:
        payload = self._payload(job_posting, profile)
        query_embedding = self.embedder.encode_json(payload)
        cursor = 0

        while True:
            cursor_response, keys = await self.redis.scan(cursor, match="resume:*", count=100)
            if isinstance(cursor_response, (bytes, str)):
                cursor_value = int(cursor_response)
            else:
                cursor_value = cursor_response
            cursor = cursor_value
            for key in keys:
                if isinstance(key, bytes):
                    key = key.decode("utf-8")
                cached_raw = await self.redis.get(key)
                if isinstance(cached_raw, bytes):
                    cached_raw = cached_raw.decode("utf-8")
                if not cached_raw:
                    continue
                cached = json.loads(cached_raw)
                cached_embedding = cached.get("embedding")
                if not cached_embedding:
                    continue
                similarity = cosine_similarity(query_embedding, cached_embedding)
                if similarity >= self.similarity_threshold:
                    resume_data = cached["resume"]
                    resume = Resume.model_validate(resume_data)
                    resume.metadata.setdefault("cached", True)
                    return resume
            if cursor_value == 0:
                break
        return None

    async def set(self, job_posting: str, profile: dict, resume: Resume) -> str:
        payload = self._payload(job_posting, profile)
        embedding = self.embedder.encode_json(payload)
        cache_key = self._cache_key(payload)
        cache_payload = {
            "resume": resume.model_dump(mode="json"),
            "embedding": embedding,
            "job_posting_preview": job_posting[:200],
            "created_at": datetime.utcnow().isoformat(),
        }
        await self.redis.setex(cache_key, self.ttl, json.dumps(cache_payload))
        return cache_key

    @staticmethod
    def _payload(job_posting: str, profile: dict) -> dict:
        return {
            "job_posting": job_posting,
            "profile": profile,
        }

    @staticmethod
    def _cache_key(payload: dict) -> str:
        digest = hashlib.md5(
            json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest()
        return f"resume:{digest}"
