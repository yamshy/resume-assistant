"""Resume generation orchestration."""

from __future__ import annotations

import json
from typing import Any, Dict, Mapping, Optional, Sequence

import tiktoken

from .agents import ResumeGenerationAgent, ResumeGenerationTools
from .cache import SemanticCache
from .llm import ResumeLLM
from .models import Resume
from .monitoring import ResumeMonitor
from .router import ModelRouter
from .validator import ClaimValidator
from .vectorstore import VectorStore


class ResumeGenerator:
    """High level orchestrator that combines caching, routing and validation."""

    def __init__(
        self,
        cache: Optional[SemanticCache],
        vector_store: VectorStore,
        llm: Optional[ResumeLLM] = None,
        router: Optional[ModelRouter] = None,
        validator: Optional[ClaimValidator] = None,
        monitor: Optional[ResumeMonitor] = None,
        confidence_threshold: float = 0.8,
        max_retries: int = 2,
    ) -> None:
        self.cache = cache
        self.vector_store = vector_store
        self.router = router or ModelRouter()
        self.validator = validator or ClaimValidator()
        self.monitor = monitor or ResumeMonitor()
        self.confidence_threshold = confidence_threshold
        self.agent = ResumeGenerationAgent(
            llm=llm,
            validator=self.validator,
            monitor=self.monitor,
            max_retries=max_retries,
            confidence_threshold=confidence_threshold,
        )

    async def generate(self, job_posting: str, user_profile: Dict[str, Any]) -> Resume:
        async def cache_lookup(job: str, profile: Dict[str, Any]) -> Optional[Resume]:
            if not self.cache:
                return None
            return await self.cache.get(job, profile)

        async def cache_store(job: str, profile: Dict[str, Any], resume: Resume) -> None:
            if self.cache and resume.confidence_scores.get("overall", 0) >= self.confidence_threshold:
                await self.cache.set(job, profile, resume)

        tools = ResumeGenerationTools(
            cache_lookup=cache_lookup if self.cache else None,
            cache_store=cache_store if self.cache else None,
            build_context=self._build_context,
            select_model=self.router.select_model,
            estimate_tokens=self._estimate_tokens,
            monitor=self.monitor.track_generation,
        )

        resume = await self.agent.generate(job_posting, user_profile, tools)
        return resume

    async def chat(
        self,
        messages: Sequence[Mapping[str, Any]],
        session: Optional[Mapping[str, Any]] = None,
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Provide conversational guidance grounded in stored best practices."""

        session_state = dict(session or {})
        turns = session_state.get("turns", 0)
        session_state["turns"] = int(turns) + 1

        last_user_message = next(
            (message for message in reversed(messages) if message.get("role") == "user"),
            None,
        )

        reply_metadata: Dict[str, Any] | None = None
        if not last_user_message or not last_user_message.get("content"):
            reply_text = "I'm here to help with your resume. What would you like to focus on?"
        else:
            query = str(last_user_message.get("content", ""))
            documents = await self.vector_store.similarity_search(query, k=1)
            if documents:
                document = documents[0]
                reply_text = (
                    "Here's guidance grounded in our resume playbook:\n"
                    f"{document.content}"
                )
                reply_metadata = {"grounding": [document.metadata | {"content": document.content}]}
            else:
                reply_text = (
                    "Focus on highlighting quantifiable achievements aligned with the job description."
                )

        reply: Dict[str, Any] = {"role": "assistant", "content": reply_text}
        if reply_metadata:
            reply["metadata"] = reply_metadata

        return reply, session_state

    async def _build_context(self, job_posting: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        combined_query = f"{job_posting}\n{json.dumps(profile, sort_keys=True, default=str)}"
        documents = await self.vector_store.similarity_search(combined_query, k=5)
        return {
            "job_posting": job_posting,
            "profile": profile,
            "retrieved_documents": [doc.metadata | {"content": doc.content} for doc in documents],
        }

    def _estimate_tokens(self, resume: Resume) -> int:
        text = resume.to_text()
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            try:
                encoding = tiktoken.get_encoding("gpt2")
            except Exception:
                return len(text.split())
        try:
            return len(encoding.encode(text))
        except Exception:
            return len(text.split())
