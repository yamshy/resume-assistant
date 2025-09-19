from datetime import date

import pytest

from app.cache import SemanticCache
from app.embeddings import SemanticEmbedder
from app.generator import ResumeGenerator
from app.llm import TemplateResumeLLM
from app.memory import InMemoryRedis
from app.router import ModelRouter
from app.validator import ClaimValidator
from app.vectorstore import VectorDocument, VectorStore


class CountingLLM(TemplateResumeLLM):
    def __init__(self):
        super().__init__()
        self.calls = 0

    async def generate(self, model: str, job_posting: str, context):  # type: ignore[override]
        self.calls += 1
        return await super().generate(model, job_posting, context)


@pytest.fixture
def profile():
    return {
        "full_name": "Taylor Candidate",
        "email": "taylor@example.com",
        "phone": "+1 555-0100",
        "location": "Remote",
        "years_experience": 6,
        "skills": ["Python", "AWS"],
        "experience": [
            {
                "company": "Acme",
                "role": "Engineer",
                "start_date": date(2018, 1, 1),
                "achievements": ["Improved system reliability by 30%"],
            }
        ],
    }


@pytest.mark.asyncio
async def test_generator_uses_cache(profile):
    embedder = SemanticEmbedder()
    redis_client = InMemoryRedis()
    cache = SemanticCache(redis_client, embedder)
    vector_store = VectorStore(embedder)
    vector_store.add_documents([VectorDocument(content="Python AWS engineer", metadata={"source": "profile"})])
    llm = CountingLLM()
    generator = ResumeGenerator(
        cache=cache,
        vector_store=vector_store,
        llm=llm,
        router=ModelRouter(),
        validator=ClaimValidator(embedder),
    )

    job_posting = "Senior Python Engineer"
    resume_first = await generator.generate(job_posting, profile)
    resume_second = await generator.generate(job_posting, profile)

    assert llm.calls == 1, "LLM should only be invoked once thanks to caching"
    assert resume_second.metadata.get("cached") is True
    assert resume_first.confidence_scores.get("overall", 0) >= 0.7
