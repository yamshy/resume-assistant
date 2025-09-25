from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Tuple, TypedDict


class VectorSearchResult(TypedDict):
    id: str
    content: str
    score: float


@dataclass(slots=True)
class VectorSearchTool:
    """Minimal, deterministic vector-like index for tests."""

    name: str = "vector_search"
    description: str = (
        "Token overlap search over previously ingested documents; deterministic and idempotent."
    )
    _documents: Dict[str, str] = field(default_factory=dict)

    def upsert(self, documents: Dict[str, str]) -> Dict[str, int]:
        """Insert or update documents in the in-memory index."""

        updated = 0
        for key, value in documents.items():
            existing = self._documents.get(key)
            if existing != value:
                self._documents[key] = value
                updated += 1
        return {"upserted": updated, "count": len(self._documents)}

    def similarity_search(self, query: str, *, top_k: int = 3) -> List[VectorSearchResult]:
        """Return the best matching documents ranked by lexical overlap."""

        if not self._documents:
            return []

        tokens = self._tokenize(query)
        scored: List[Tuple[float, str, str]] = []
        result: List[VectorSearchResult] = []
        for doc_id, content in self._documents.items():
            overlap = self._overlap(tokens, self._tokenize(content))
            if overlap > 0:
                scored.append((overlap, doc_id, content))
        scored.sort(reverse=True)
        top_results = scored[:top_k]
        for score, doc_id, content in top_results:
            result.append(
                {
                    "id": doc_id,
                    "content": content,
                    "score": round(score, 4),
                }
            )
        return result

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return [token for token in text.lower().split() if token]

    @staticmethod
    def _overlap(query_tokens: Iterable[str], doc_tokens: Iterable[str]) -> float:
        query_set = set(query_tokens)
        doc_set = set(doc_tokens)
        if not query_set or not doc_set:
            return 0.0
        shared = len(query_set & doc_set)
        return shared / float(len(query_set))


__all__ = ["VectorSearchTool"]
