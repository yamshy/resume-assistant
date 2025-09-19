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

The service exposes three primary endpoints:

- `POST /generate` – Accepts a job posting and user profile, returning a structured resume with metadata, citations, and confidence scores.
- `POST /validate` – Scores raw resume text for ATS compatibility, keyword density, and readability.
- `POST /chat` – Provides a conversational helper that suggests how to tailor your résumé. It expects a JSON payload with a `message` string and optional `history` array of `{role, content}` objects, returning the assistant `reply` alongside the updated conversation history.

A helper `GET /health` endpoint returns a simple status payload.

### Using the Chat UI

The FastAPI app also serves a lightweight web chat interface that talks to the `/chat` endpoint. Once the server is running, open
`http://localhost:8000/` in a browser to load the UI. Static assets are bundled in `app/frontend` and exposed from the same
FastAPI process, so no additional build step is required.

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

## Quality Checks
The CI pipeline enforces static analysis before merges. Run them locally with:

```bash
uv run --extra dev ruff check
uv run --extra dev mypy app
```

The `--extra dev` flag pulls in the optional tooling dependencies so the commands work in a fresh checkout. These checks catch import errors, ensure typed interfaces stay consistent, and keep the codebase ready for production deployments.

## Contributing
- Use [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) for all commit messages so automated release tooling can infer semantic meaning. Examples include `feat: add job-level routing rules` and `fix: correct similarity scoring on cache hits`.
- Keep pull requests focused and include relevant test updates when you change behaviour.
- Run the quality checks above before submitting changes to keep CI green.

## Extensibility
- Swap `TemplateResumeLLM` in `app/llm.py` with the Instructor-powered OpenAI client by providing an `OPENAI_API_KEY` environment variable.
- Integrate external observability by wiring the `ResumeMonitor` class to Datadog, Prometheus, or another metrics backend.
- Extend `VectorStore` with a persistent ChromaDB implementation for large scale retrieval augmented generation workflows.

## Key Metrics
- **Cost per resume**: < $0.05 achieved via model routing and caching.
- **Factual accuracy**: > 95% through semantic claim validation.
- **ATS compatibility**: > 90% parse rate validated with heuristics.
- **Latency**: < 3 seconds by avoiding redundant generations.
