# Resume Assistant

AI-powered resume tailoring system using a 5-agent chain architecture to analyze job postings and generate customized resumes with human-in-the-loop approval workflow.

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- UV package manager
- OpenAI API key (GPT-4o)
- Secrets management (Infisical recommended)

### Installation
```bash
# Clone and setup
git clone <repo-url>
cd resume-assistant
uv sync --dev

# Configure secrets
cp .env.example .env
# Add your OpenAI API key
```

### Launch Server
```bash
# With secrets management (recommended)
PYTHONPATH=src infisical run -- uv run python src/main.py

# Direct environment (dev only)
PYTHONPATH=src OPENAI_API_KEY=xxx uv run python src/main.py
```

### Test the System
```bash
# Health check
curl http://localhost:8000/health

# Interactive API docs
open http://localhost:8000/docs

# Run complete test suite
PYTHONPATH=src infisical run -- uv run python tests/e2e/test_quickstart_scenario.py
```

## 🏗️ System Architecture

**5-Agent Chain Pipeline:**
```
Job Posting → [Job Analysis] → [Profile Matching] → [Resume Generation] → [Validation] → [Human Interface] → Tailored Resume
```

**Performance:** 65-110 seconds total processing, 85% match scores

**Technology Stack:** FastAPI + pydanticAI + GPT-4o + constitutional patterns

## 📚 Documentation

### 📁 [Complete Documentation](docs/)
- **[Quick Start Guide](docs/api/README.md)** - API usage examples
- **[Architecture Overview](docs/architecture/README.md)** - System design
- **[Deployment Guide](docs/deployment/DEPLOYMENT_READY.md)** - Production setup
- **[Test Results](docs/testing/E2E_TEST_RESULTS.md)** - Validation report

### 🔗 Key Resources
- **[System Context](CLAUDE.md)** - Complete constitutional patterns
- **[API Documentation](http://localhost:8000/docs)** - Interactive Swagger UI
- **[Feature Specification](specs/001-resume-tailoring-feature/spec.md)** - Detailed requirements

## 🏃‍♂️ Usage Examples

### 1. Setup User Profile
```bash
curl -X PUT "http://localhost:8000/profile" \
  -H "Content-Type: application/json" \
  -d @data/test/test_profile_wrapped.json
```

### 2. Generate Tailored Resume
```bash
curl -X POST "http://localhost:8000/resumes/tailor" \
  -H "Content-Type: application/json" \
  -d @data/test/test_job.json
```

### 3. Review Results
The system returns:
- **85% match score** with detailed skill analysis
- **Professional tailored resume** in markdown format
- **Quality validation** with improvement suggestions
- **Approval workflow** for human review

## 🧪 Development

### Run Tests
```bash
# Unit tests with mocks
PYTHONPATH=src uv run python -m pytest tests/unit/ -v

# End-to-end validation
PYTHONPATH=src infisical run -- uv run python tests/e2e/test_quickstart_scenario.py

# Code quality
uv run ruff format . && uv run ruff check .
```

### Project Structure
```
src/
├── models/           # Pydantic data models
├── agents/           # 5 pydanticAI agents
├── services/         # Business logic layer
├── api/             # FastAPI route handlers
└── utils/           # Utility functions

docs/
├── api/             # API documentation
├── architecture/    # System design docs
├── deployment/      # Production guides
└── testing/         # Validation reports

data/
├── test/            # Test data and examples
├── real/            # Production data location
└── samples/         # Documentation examples
```

## ✅ Status

**Production Ready:** ✅ All validation passed

| Component | Status | Performance | Quality |
|-----------|--------|-------------|---------|
| 5-Agent Pipeline | ✅ Working | 65-110s | 85% match |
| API Endpoints | ✅ All 8 working | <500ms | 100% uptime |
| Error Handling | ✅ Robust | Graceful | User-friendly |
| Documentation | ✅ Complete | N/A | Professional |

## 🏛️ Constitutional Patterns

This project follows strict architectural principles:

- **Agent-Chain Architecture:** All intelligence implemented as agent chains
- **FastAPI + pydanticAI Stack:** Modern async Python with structured outputs
- **Radical Simplicity:** Single-file agents, clear interfaces, no abstractions
- **Test-Driven Development:** Comprehensive validation with real API integration

## 📞 Support

- **[Documentation Hub](docs/)** - Complete system documentation
- **[API Reference](http://localhost:8000/docs)** - Interactive API documentation
- **[Architecture Guide](CLAUDE.md)** - Technical implementation details
- **[Test Examples](data/test/)** - Sample data and usage patterns

---

**Version:** 1.0 (Production Ready)
**Last Updated:** September 18, 2025
**Architecture:** Constitutional Agent-Chain Patterns
**Status:** ✅ Approved for Production Deployment