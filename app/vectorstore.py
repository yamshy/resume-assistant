"""Lightweight vector store abstraction wrapping Chroma like behaviour."""

from __future__ import annotations

import heapq
from dataclasses import dataclass
from typing import Iterable, List

from .embeddings import SemanticEmbedder
from .utils import cosine_similarity


@dataclass
class VectorDocument:
    content: str
    metadata: dict


class InMemoryVectorStore:
    """Simple in-memory vector store for unit testing and local runs."""

    def __init__(self, embedder: SemanticEmbedder | None = None) -> None:
        self.embedder = embedder or SemanticEmbedder()
        self._documents: List[VectorDocument] = []
        self._embeddings: List[List[float]] = []

    def add_documents(self, documents: Iterable[VectorDocument]) -> None:
        docs = list(documents)
        if not docs:
            return
        self._documents.extend(docs)
        embeddings = self.embedder.encode(doc.content for doc in docs)
        self._embeddings.extend(embeddings)

    async def similarity_search(self, query: str, k: int = 5) -> List[VectorDocument]:
        if not self._documents:
            return []
        query_embedding = self.embedder.encode([query])[0]
        scored = []
        for doc, embedding in zip(self._documents, self._embeddings):
            score = cosine_similarity(query_embedding, embedding)
            heapq.heappush(scored, (score, doc))
            if len(scored) > k:
                heapq.heappop(scored)
        scored.sort(reverse=True)
        return [doc for _, doc in scored]


VectorStore = InMemoryVectorStore
