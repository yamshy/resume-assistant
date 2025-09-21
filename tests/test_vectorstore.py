import pytest

from app.vectorstore import InMemoryVectorStore, VectorDocument


class ConstantEmbedder:
    """Simple embedder returning the same embedding for every input."""

    def encode(self, texts):
        if isinstance(texts, str):
            texts = [texts]
        texts = list(texts)
        return [[1.0, 0.0] for _ in texts]


@pytest.mark.asyncio
async def test_similarity_search_handles_equal_scores():
    store = InMemoryVectorStore(embedder=ConstantEmbedder())
    documents = [
        VectorDocument(content="doc-1", metadata={"id": 1}),
        VectorDocument(content="doc-2", metadata={"id": 2}),
    ]
    store.add_documents(documents)

    results = await store.similarity_search("any query", k=2)

    assert results == documents
