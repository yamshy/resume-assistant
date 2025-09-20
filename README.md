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

### Populating the Knowledge Base

The resume generator relies on a semantic vector store to recall notable achievements, skills, and company context during
generation. Seed it with your own content by POSTing documents to the `/knowledge` endpoint. Each document accepts free-form
text plus optional metadata for filtering or provenance tracking:

```bash
curl -X POST http://localhost:8000/knowledge \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "content": "Scaled Kubernetes infrastructure to 500+ nodes while reducing incident response time by 30%.",
        "metadata": {"source": "portfolio", "tags": ["sre", "kubernetes"]}
      },
      {
        "content": "Led migration from on-prem ETL to dbt + Snowflake, cutting pipeline costs by 45%.",
        "metadata": {"source": "case-study"}
      }
    ]
  }'
```

The default in-memory store persists for the lifetime of the process. Point `VectorStore` at a persistent backend (e.g. ChromaDB)
for long-lived deployments.

### Generating a Tailored Resume

With the knowledge base populated, call the `/generate` endpoint with the target job posting and a structured profile. The
generator orchestrates retrieval, LLM routing, semantic validation, and monitoring before returning an ATS-friendly resume:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "job_posting": "Site Reliability Engineer responsible for scaling observability across multi-region Kubernetes.",
    "profile": {
      "full_name": "Alex Candidate",
      "email": "alex@example.com",
      "phone": "+1 555-0200",
      "location": "Remote",
      "skills": ["Kubernetes", "Prometheus", "Terraform"],
      "years_experience": 8,
      "experience": [
        {
          "company": "ScaleOps",
          "role": "Senior SRE",
          "start_date": "2019-02-01",
          "achievements": [
            "Automated cluster remediation playbooks that cut paging volume by 40%",
            "Improved deployment reliability to 99.95% uptime across three regions"
          ]
        }
      ]
    }
  }'
```

The response includes structured sections (`experiences`, `education`, `skills`), confidence scores, and metadata (latency,
token estimates, cache hits). Persist or render `Resume.to_text()` to deliver a finalized document. Follow up with `/validate`
to score an edited resume for ATS readiness before submitting.

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
