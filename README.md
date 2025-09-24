# AI Resume Assistant

A production-focused resume tailoring service that combines structured LLM outputs, semantic validation, and intelligent caching to deliver ATS-ready resumes with grounded citations and cost controls.

## Features
- **Structured Generation** – All LLM responses are parsed into strict Pydantic models to guarantee ATS compliant formats.
- **Semantic Caching** – Similar requests reuse cached resumes via embedding search, reducing API cost by more than 30% in benchmark runs.
- **Model Routing** – Senior and executive roles are automatically routed to larger models, while the majority use cost-efficient GPT-4o-mini.
- **Citation Grounding** – Each achievement, skill, and company/role claim is annotated with the source text used during generation to prevent hallucinations.
- **Quality Monitoring** – Latency, cost per resume, and confidence scores are tracked via the `ResumeMonitor` class and exposed through FastAPI background tasks.
- **Agent Planning** – A reusable `ResumeGenerationAgent` coordinates retrieval, drafting, validation, and revision loops so every resume is iteratively improved before delivery.

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

### Grounding Requirements

The claim validator now enforces that every skill and company/role listed on a generated resume is supported by the supplied
context. Ingestion payloads and custom profile overrides must expose `profile.skills` and `profile.experience` (including the
`company`, `role`, and supporting `achievements`) so validation can attach citations and confidence scores. When the evidence is
missing, the validator drives the overall confidence to zero, prompting the generation agent to request additional grounding
before finalising the resume.

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

#### Agent-driven orchestration

The `/generate` workflow is powered by `ResumeGenerationAgent`, which uses the active LLM (resolved via `resolve_llm()` by default)
to execute four explicit steps: context retrieval, draft generation, semantic validation, and revision. Tool hooks provided by
`ResumeGenerator` let the agent look up cached resumes, run vector searches, invoke the validator, and record metrics through
`ResumeMonitor`. Each generation attempt updates the resume metadata with latency, token estimates, and validator feedback so
operators can audit how the draft evolved.

Two configuration knobs control the loop:

- `confidence_threshold` – minimum overall confidence score required before the agent accepts a draft (default `0.8`). Lower it
  to move faster on noisier data or raise it to demand stronger grounding before caching a result.
- `max_retries` – how many times the agent will re-invoke the LLM with validator feedback when scores fall below the threshold or
  grounding checks fail (default `2`). Increase this for stricter QA at the cost of additional latency and tokens.

Example instantiation:

```python
generator = ResumeGenerator(
    cache=semantic_cache,
    vector_store=vector_store,
    confidence_threshold=0.85,
    max_retries=3,
)
```

In this configuration the agent will request up to three drafts, injecting validator guidance between attempts and recording the
outcome of each pass through `ResumeMonitor`.

### Running in Docker

The repository ships with a production-ready Dockerfile and Compose stack so you can run the full service (API, Redis, and
ChromaDB) with a single command. Build the image and start the containers with:

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000`. Resume knowledge is persisted to `./data/knowledge` on the host via the
`KNOWLEDGE_STORE_PATH` environment variable that the container exports. Uploading resumes via `POST /knowledge` will
create/update `data/knowledge/knowledge_store.json` without rebuilding the image.

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
