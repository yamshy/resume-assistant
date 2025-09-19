"""Semantic validation utilities for generated resumes."""

from __future__ import annotations

from typing import Dict, Iterable, List

from .embeddings import SemanticEmbedder
from .models import Resume
from .utils import cosine_similarity


class ClaimValidator:
    """Validate resume claims are grounded in provided context."""

    def __init__(self, embedder: SemanticEmbedder | None = None, threshold: float = 0.7) -> None:
        self.embedder = embedder or SemanticEmbedder()
        self.threshold = threshold

    async def validate(self, resume: Resume, context: Dict[str, object]) -> Resume:
        context_snippets = self._flatten_context(context)
        if not context_snippets:
            resume.confidence_scores["overall"] = 0.0
            return resume

        context_embeddings = self.embedder.encode(context_snippets)

        overall_scores: List[float] = []
        for experience in resume.experiences:
            for achievement in experience.achievements:
                achievement_embedding = self.embedder.encode([achievement])[0]
                similarity, citation = self._max_similarity(achievement_embedding, context_embeddings, context_snippets)
                resume.confidence_scores[achievement] = similarity
                if citation:
                    resume.citations.setdefault(achievement, citation)
                overall_scores.append(similarity)

        if overall_scores:
            resume.confidence_scores["overall"] = min(overall_scores)
        else:
            resume.confidence_scores.setdefault("overall", 0.0)
        return resume

    def _flatten_context(self, context: Dict[str, object]) -> List[str]:
        snippets: List[str] = []
        for key, value in context.items():
            snippets.extend(self._stringify(value))
        return [snippet for snippet in snippets if snippet]

    def _stringify(self, value: object) -> Iterable[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, dict):
            return [snippet for nested in value.values() for snippet in self._stringify(nested)]
        if isinstance(value, list):
            return [snippet for item in value for snippet in self._stringify(item)]
        return [str(value)]

    @staticmethod
    def _max_similarity(
        embedding,
        context_embeddings: List[List[float]],
        snippets: List[str],
    ) -> tuple[float, str | None]:
        best_score = 0.0
        best_snippet = None
        for snippet, context_embedding in zip(snippets, context_embeddings):
            score = cosine_similarity(embedding, context_embedding)
            if score > best_score:
                best_score = score
                best_snippet = snippet
        return best_score, best_snippet
