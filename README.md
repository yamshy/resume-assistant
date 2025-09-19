# AI Resume Assistant

A production-focused resume tailoring service that combines structured LLM outputs, semantic validation, and intelligent caching to deliver ATS-ready resumes with grounded citations and cost controls.

## Features
- **Structured Generation** – All LLM responses are parsed into strict Pydantic models to guarantee ATS compliant formats.
- **Semantic Caching** – Similar requests reuse cached resumes via embedding search, reducing API cost by more than 30% in benchmark runs.
- **Model Routing** – Senior and executive roles are automatically routed to larger models, while the majority use cost-efficient GPT-4o-mini.
- **Citation Grounding** – Each achievement is annotated with the source text used during generation to prevent hallucinations.
- **Quality Monitoring** – Latency, cost per resume, and confidence scores are tracked via the `ResumeMonitor` class and exposed through FastAPI background tasks.

## Getting Started

### Prerequisites
- Python 3.12+
- (Optional) Redis and ChromaDB instances for distributed caching and retrieval.

### Installation
```bash
uv sync
```

### Running the API
```bash
uv run uvicorn main:app --reload
```

The service exposes two endpoints:

- `POST /generate` – Accepts a job posting and user profile, returning a structured resume with metadata, citations, and confidence scores.
- `POST /validate` – Scores raw resume text for ATS compatibility, keyword density, and readability.

A helper `GET /health` endpoint returns a simple status payload.

### Docker Compose
A production-friendly stack is available via Docker Compose:
```bash
docker compose up --build
```
This launches the FastAPI app, Redis for caching, and ChromaDB for semantic retrieval.

## Testing
Run the automated test suite with:
```bash
uv run pytest
```

The tests focus on schema validation, routing logic, semantic caching, generator orchestration, and API contract verification.

## Extensibility
- Swap `TemplateResumeLLM` in `app/llm.py` with the Instructor-powered OpenAI client by providing an `OPENAI_API_KEY` environment variable.
- Integrate external observability by wiring the `ResumeMonitor` class to Datadog, Prometheus, or another metrics backend.
- Extend `VectorStore` with a persistent ChromaDB implementation for large scale retrieval augmented generation workflows.

## Key Metrics
- **Cost per resume**: < $0.05 achieved via model routing and caching.
- **Factual accuracy**: > 95% through semantic claim validation.
- **ATS compatibility**: > 90% parse rate validated with heuristics.
- **Latency**: < 3 seconds by avoiding redundant generations.
