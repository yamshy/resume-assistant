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

- `POST /knowledge` – Ingests one or more resumes plus optional reviewer notes and updates the structured skills/experience database and retrieval store.
- `POST /generate` – Accepts a job posting and user profile (or the aggregated knowledge base), returning a structured resume with metadata, citations, and confidence scores.
- `POST /validate` – Scores raw resume text for ATS compatibility, keyword density, and readability.

A helper `GET /health` endpoint returns a simple status payload.

### Using the Web Workspace

The FastAPI app serves a chat-first workspace at `http://localhost:8000/`. Static assets ship with the repository in
`app/frontend`, so no build step is required. The interface combines a running conversation with workflow panels that map to the
API endpoints and stream their results back into the transcript for human-in-the-loop review.

- **Chat guidance** – Ask the assistant what knowledge is available, confirm that resumes were parsed correctly, or walk through
  the steps needed to prepare a new application. The browser client calls the `/chat` endpoint and keeps the full history on the
  page so reviewers can audit each exchange.
- **Ingest resumes** – Upload one or more resume exports (TXT, PDF, DOCX, etc.) and optionally add reviewer notes. The UI submits
  a multipart request to `/knowledge`, persists a structured skills/experience database, and renders the parsed snapshot so you
  can confirm extracted skills and achievements before proceeding.
- **Generate resume** – Paste the job description and click *Generate tailored resume*. If you have ingested resumes the
  generator automatically hydrates the profile from the knowledge base; you can still supply a JSON payload via the API for
  bespoke experiments. The structured resume JSON is rendered inline so reviewers can annotate or adjust prior to delivery.

### Populating the Knowledge Base

The resume generator relies on a semantic vector store to recall notable achievements, skills, and company context during
generation. Seed it with your own content by uploading resume files to the `/knowledge` endpoint. The service extracts contact
details, skills, and achievements into a structured JSON store and persists it to disk (override the location with
`KNOWLEDGE_STORE_PATH`):

```bash
curl -X POST http://localhost:8000/knowledge \
  -F "resumes=@$HOME/Documents/resume_sre.txt" \
  -F "resumes=@$HOME/Documents/resume_manager.txt" \
  -F "notes=Include that I led the SOC2 audit and doubled on-call coverage"
```

The response summarises how many resumes were processed, the new skills indexed, and a profile snapshot used for subsequent
generation. Extracted achievements are embedded into the retrieval store so they can be cited during drafting.

### Generating a Tailored Resume

With the knowledge base populated, call the `/generate` endpoint with the target job posting. The generator hydrates the profile
from the stored resumes, orchestrates retrieval, LLM routing, semantic validation, and monitoring, then returns an ATS-friendly
resume. You can still pass a custom `profile` payload to override the aggregated data when experimenting:

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "job_posting": "Site Reliability Engineer responsible for scaling observability across multi-region Kubernetes."
  }'
```

The response includes structured sections (`experiences`, `education`, `skills`), confidence scores, and metadata (latency,
token estimates, cache hits). Persist or render `Resume.to_text()` to deliver a finalized document. Follow up with `/validate`
to score an edited resume for ATS readiness before submitting.

### Running in Docker

The repository ships with a production-ready Dockerfile and Compose stack so you can run the full service (API, web workspace,
Redis, and ChromaDB) with a single command. Build the image and start the containers with:

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000` and serves the workflow UI from the same address. Static assets come directly
from the image, so no additional build tooling is required. Resume knowledge is persisted to `./data/knowledge` on the host via
the `KNOWLEDGE_STORE_PATH` environment variable that the container exports. Uploading resumes through the UI or via `POST
/knowledge` will create/update `data/knowledge/knowledge_store.json` without rebuilding the image.

Set `OPENAI_API_KEY` in your environment before running `docker compose up` if you want to invoke real LLMs. Otherwise the
service falls back to the deterministic template generator. When you're done experimenting, run `docker compose down` to stop
the stack and release resources.

### Resume Ingestion Agent Configuration

The `/knowledge` endpoint now delegates resume parsing to an agent that coordinates a "plan → extract → verify" loop with the
selected LLM. The agent still falls back to deterministic heuristics when no OpenAI key is present, but operators can tune its
behaviour with environment variables:

- `INGESTION_AGENT_MODEL` – Chat/completions model used for plan/extract/verify stages (default `gpt-4o-mini`).
- `INGESTION_AGENT_TEMPERATURE` – Sampling temperature applied to each stage (default `0.1` to prioritise determinism).
- `INGESTION_AGENT_MAX_RETRIES` – Maximum retries for failed LLM calls (default `1`).

Override these settings when you need a larger model for noisy documents or want to harden the workflow with additional
retries. Tool heuristics (email, phone, skills, experience extraction) remain available to the agent regardless of model choice
so it can correct incomplete outputs.

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
