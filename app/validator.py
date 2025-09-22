"""Semantic validation utilities for generated resumes."""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Sequence

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
        semantic_supported = bool(getattr(self.embedder, "_model", None)) and not getattr(
            self.embedder, "_load_failed", False
        )
        snippet_tokens = [self._tokenize(self._normalize(snippet)) for snippet in context_snippets]
        tokenized_context = list(zip(context_snippets, snippet_tokens))

        profile = self._extract_profile(context)
        skill_sources = self._collect_skill_sources(context, profile)
        experience_entries = self._collect_experience_entries(context, profile)
        company_sources, role_sources = self._collect_experience_sources(experience_entries)

        overall_scores: List[float] = []

        def record_score(key: str, raw_score: float, citation: str | None) -> None:
            score = self._apply_threshold(raw_score)
            resume.confidence_scores[key] = score
            if citation and score > 0:
                resume.citations.setdefault(key, citation)
            overall_scores.append(score)

        for experience in resume.experiences:
            for achievement in experience.achievements:
                achievement_embedding = self.embedder.encode([achievement])[0]
                similarity, citation = self._max_similarity(
                    achievement_embedding, context_embeddings, context_snippets
                )
                record_score(achievement, similarity, citation)

        for skill in resume.skills:
            score, citation = self._evaluate_claim(
                claim=skill,
                direct_sources=skill_sources,
                context_embeddings=context_embeddings,
                context_snippets=context_snippets,
                tokenized_context=tokenized_context,
                allow_semantic=semantic_supported,
            )
            record_score(f"skill:{skill}", score, citation)

        for experience in resume.experiences:
            company_key = f"experience.company:{experience.company}"
            company_score, company_citation = self._evaluate_claim(
                claim=experience.company,
                direct_sources=company_sources,
                context_embeddings=context_embeddings,
                context_snippets=context_snippets,
                tokenized_context=tokenized_context,
                allow_semantic=semantic_supported,
            )
            record_score(company_key, company_score, company_citation)

            role_claim = f"{experience.role} at {experience.company}" if experience.company else experience.role
            role_key = f"experience.role:{experience.role} at {experience.company}"
            role_score, role_citation = self._evaluate_claim(
                claim=role_claim,
                direct_sources=role_sources,
                context_embeddings=context_embeddings,
                context_snippets=context_snippets,
                tokenized_context=tokenized_context,
                allow_semantic=semantic_supported,
            )
            record_score(role_key, role_score, role_citation)

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

    def _extract_profile(self, context: Dict[str, object]) -> Dict[str, object]:
        profile = context.get("profile")
        if isinstance(profile, dict):
            return profile
        return {}

    def _collect_skill_sources(
        self, context: Dict[str, object], profile: Dict[str, object]
    ) -> List[tuple[str, str]]:
        sources: List[tuple[str, str]] = []
        for container in (context.get("skills"), profile.get("skills")):
            for value in self._iter_strings(container):
                normalized = self._normalize(value)
                if normalized:
                    sources.append((normalized, value))
        return sources

    def _collect_experience_entries(
        self, context: Dict[str, object], profile: Dict[str, object]
    ) -> List[Dict[str, object]]:
        entries: List[Dict[str, object]] = []
        for container in (context.get("experience"), profile.get("experience")):
            if isinstance(container, list):
                for value in container:
                    if isinstance(value, dict):
                        entries.append(value)
        return entries

    def _collect_experience_sources(
        self, entries: Sequence[Dict[str, object]]
    ) -> tuple[List[tuple[str, str]], List[tuple[str, str]]]:
        company_sources: List[tuple[str, str]] = []
        role_sources: List[tuple[str, str]] = []
        for entry in entries:
            company = entry.get("company")
            role = entry.get("role")
            if isinstance(company, str) and company.strip():
                normalized_company = self._normalize(company)
                if normalized_company:
                    company_sources.append((normalized_company, company))
            if isinstance(role, str) and role.strip():
                if isinstance(company, str) and company.strip():
                    citation = f"{role} at {company}"
                else:
                    citation = role
                normalized_role = self._normalize(citation)
                if normalized_role:
                    role_sources.append((normalized_role, citation))
        return company_sources, role_sources

    def _evaluate_claim(
        self,
        claim: str,
        *,
        direct_sources: Sequence[tuple[str, str]],
        context_embeddings: List[List[float]],
        context_snippets: List[str],
        tokenized_context: Sequence[tuple[str, set[str]]],
        allow_semantic: bool,
    ) -> tuple[float, str | None]:
        normalized_claim = self._normalize(claim)
        if not normalized_claim:
            return 0.0, None

        for source_value, citation in direct_sources:
            if normalized_claim == source_value:
                return 1.0, citation

        claim_tokens = self._tokenize(normalized_claim)
        for snippet, tokens in tokenized_context:
            if claim_tokens and (claim_tokens <= tokens or tokens <= claim_tokens):
                return 1.0, snippet

        if not allow_semantic:
            return 0.0, None

        claim_embedding = self.embedder.encode([claim])[0]
        return self._max_similarity(claim_embedding, context_embeddings, context_snippets)

    def _apply_threshold(self, score: float) -> float:
        if score < self.threshold:
            return 0.0
        return score

    def _iter_strings(self, value: object) -> Iterable[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value] if value.strip() else []
        if isinstance(value, (list, tuple, set)):
            return [item for item in value if isinstance(item, str) and item.strip()]
        return []

    def _normalize(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

    def _tokenize(self, normalized_value: str) -> set[str]:
        if not normalized_value:
            return set()
        return {token for token in normalized_value.split(" ") if token}

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
