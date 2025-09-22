"""Agent-driven orchestration for resume generation."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Optional, Sequence

from ..llm import ResumeLLM, resolve_llm
from ..models import Resume
from ..monitoring import ResumeMonitor
from ..validator import ClaimValidator

CacheLookup = Callable[[str, Dict[str, Any]], Awaitable[Resume | None]]
CacheStore = Callable[[str, Dict[str, Any], Resume], Awaitable[None]]
ContextBuilder = Callable[[str, Dict[str, Any]], Awaitable[Dict[str, Any]]]
ModelSelector = Callable[[str, Dict[str, Any]], str]
TokenEstimator = Callable[[Resume], int]
MonitorHook = Callable[[str, int, float, float, bool], Awaitable[None]]
Timer = Callable[[], float]


@dataclass(slots=True)
class ResumeGenerationTools:
    """Async hooks used by :class:`ResumeGenerationAgent`."""

    cache_lookup: CacheLookup | None = None
    cache_store: CacheStore | None = None
    build_context: ContextBuilder | None = None
    select_model: ModelSelector | None = None
    estimate_tokens: TokenEstimator | None = None
    monitor: MonitorHook | None = None
    now: Timer = time.perf_counter


class ResumeGenerationAgent:
    """Stateful planner that coordinates resume generation attempts."""

    def __init__(
        self,
        llm: ResumeLLM | None = None,
        validator: ClaimValidator | None = None,
        monitor: ResumeMonitor | None = None,
        *,
        max_retries: int = 2,
        confidence_threshold: float = 0.8,
    ) -> None:
        self.llm = llm or resolve_llm()
        self.validator = validator or ClaimValidator()
        self.monitor = monitor or ResumeMonitor()
        self.max_retries = max(1, max_retries)
        self.confidence_threshold = confidence_threshold
        self.plan_steps: Sequence[str] = (
            "context_retrieval",
            "draft_generation",
            "validation",
            "revision",
        )

    async def generate(
        self,
        job_posting: str,
        profile: Dict[str, Any],
        tools: ResumeGenerationTools,
    ) -> Resume:
        """Execute the planning loop until validation succeeds or retries are exhausted."""

        monitor_hook = tools.monitor or self.monitor.track_generation
        cached = await self._check_cache(job_posting, profile, tools, monitor_hook)
        if cached is not None:
            return cached

        if tools.build_context is None:
            raise ValueError("A context builder tool is required for resume generation")
        if tools.select_model is None:
            raise ValueError("A model selection tool is required for resume generation")

        base_context = await tools.build_context(job_posting, profile)
        feedback: Optional[str] = None
        last_resume: Optional[Resume] = None

        for attempt in range(1, self.max_retries + 1):
            attempt_context = dict(base_context)
            if feedback:
                attempt_context["validator_feedback"] = feedback

            model = tools.select_model(job_posting, profile)
            start_time = tools.now()
            resume = await self.llm.generate(model, job_posting, attempt_context)
            latency = tools.now() - start_time

            resume.metadata["plan"] = list(self.plan_steps)
            resume.metadata["model"] = model
            resume.metadata["cached"] = False
            resume.metadata["latency"] = latency
            resume.metadata["attempt"] = attempt
            resume.metadata["attempts"] = attempt

            tokens = self._estimate_tokens(resume, tools)
            resume.metadata["tokens"] = tokens

            resume = await self.validator.validate(resume, base_context)
            overall_confidence = float(resume.confidence_scores.get("overall", 0.0))
            missing_citations = self._missing_citations(resume)
            validation_passed = (
                overall_confidence >= self.confidence_threshold and not missing_citations
            )

            await monitor_hook(model, tokens, latency, overall_confidence, False)

            if validation_passed:
                resume.metadata["validation_passed"] = True
                resume.metadata.pop("validator_feedback", None)
                if tools.cache_store is not None:
                    await tools.cache_store(job_posting, profile, resume)
                return resume

            feedback = self._build_feedback(overall_confidence, missing_citations)
            resume.metadata["validation_passed"] = False
            resume.metadata["validator_feedback"] = feedback
            last_resume = resume

        if last_resume is None:  # pragma: no cover - defensive, loop guarantees assignment
            raise RuntimeError("Generation attempts did not yield a resume")
        return last_resume

    async def _check_cache(
        self,
        job_posting: str,
        profile: Dict[str, Any],
        tools: ResumeGenerationTools,
        monitor_hook: MonitorHook,
    ) -> Resume | None:
        if tools.cache_lookup is None:
            return None

        cached_resume = await tools.cache_lookup(job_posting, profile)
        if cached_resume is None:
            return None

        cached_resume.metadata["plan"] = list(self.plan_steps)
        cached_resume.metadata["cached"] = True
        cached_resume.metadata.setdefault("latency", 0.0)
        tokens = self._estimate_tokens(cached_resume, tools)
        cached_resume.metadata.setdefault("tokens", tokens)
        cached_resume.metadata.setdefault("attempts", 0)

        if "model" not in cached_resume.metadata and tools.select_model is not None:
            cached_resume.metadata["model"] = tools.select_model(job_posting, profile)

        model_name = str(cached_resume.metadata.get("model", "unknown"))
        overall_confidence = float(cached_resume.confidence_scores.get("overall", 0.0))
        await monitor_hook(
            model_name,
            int(cached_resume.metadata.get("tokens", tokens)),
            float(cached_resume.metadata.get("latency", 0.0)),
            overall_confidence,
            True,
        )
        return cached_resume

    def _estimate_tokens(self, resume: Resume, tools: ResumeGenerationTools) -> int:
        if tools.estimate_tokens is not None:
            try:
                return int(tools.estimate_tokens(resume))
            except Exception:  # pragma: no cover - defensive fallback
                pass
        return len(resume.to_text().split())

    @staticmethod
    def _missing_citations(resume: Resume) -> List[str]:
        missing: List[str] = []
        provided = resume.citations or {}
        for experience in resume.experiences:
            for achievement in experience.achievements:
                if achievement not in provided:
                    missing.append(achievement)
        return missing

    def _build_feedback(self, overall: float, missing_citations: Iterable[str]) -> str:
        messages: List[str] = []
        if overall < self.confidence_threshold:
            messages.append(
                (
                    "Overall confidence {:.2f} is below the threshold {:.2f}. "
                    "Improve grounding or provide additional context."
                ).format(overall, self.confidence_threshold)
            )
        missing = list(missing_citations)
        if missing:
            messages.append(
                "Provide citations or evidence for these achievements: "
                + ", ".join(missing[:5])
            )
        if not messages:
            messages.append("Refine the resume using validator feedback.")
        return "\n".join(messages)
