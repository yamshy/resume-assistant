# Resume Assistant Template

Minimal FastAPI + pydanticAI template with TDD workflow and src layout.

## Quickstart

### Prerequisites

- Python 3.12+
- uv (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone <repo-url>
cd resume-assistant-template
```

2. Install dependencies:
```bash
uv pip install -e .[dev]
```

3. Copy environment variables:
```bash
cp .env.example .env
```

## Commands

### Development

```bash
# Install development dependencies
uv pip install -e .[dev]

# Run tests
uv run pytest -q

# Format code
uv run ruff format .

# Check linting
uv run ruff check .

# Run development server
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Use CLI
uv run resume-assistant --help
```

### Testing

```bash
# Run all tests
uv run pytest -q

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/unit/test_health.py
```

### Production

```bash
# Run with uvicorn
uv run uvicorn app.main:app --host 0.0.0.0 --port 8080

# Run with CLI
uv run resume-assistant --host 0.0.0.0 --port 8080
```

## Project Structure

```
.
├── app/                    # FastAPI application
│   ├── api/               # API routes
│   ├── core/              # Core application config
│   └── main.py            # Application entry point
├── src/resume_core/       # Library package
│   ├── agents/            # AI agent implementations
│   └── services/          # Business logic services
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
└── pyproject.toml         # Project configuration
```

## API Endpoints

- `GET /api/v1/health` - Health check endpoint

## Environment Variables

- `OPENAI_API_KEY` - OpenAI API key (optional, mocked in tests)
- `ENV` - Environment (dev/staging/prod)
- `MODEL_NAME` - AI model to use (default: gpt-4o)
- `DEBUG` - Debug mode (true/false)

## License

MIT