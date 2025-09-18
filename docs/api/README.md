# API Documentation

## Quick Reference

**Base URL:** `http://localhost:8000`

## Core Endpoints

### Health & Info
```bash
GET  /                    # System information
GET  /health             # Health check status
GET  /docs               # Interactive API documentation
```

### Profile Management
```bash
GET  /profile            # Retrieve stored user profile
PUT  /profile            # Save/update user profile
```

### Resume Tailoring
```bash
POST /jobs/analyze       # Analyze job posting (5-10s)
POST /resumes/tailor     # Complete tailoring pipeline (65-110s)
```

## Usage Examples

### 1. Setup Profile
```bash
curl -X PUT "http://localhost:8000/profile" \
  -H "Content-Type: application/json" \
  -d @data/test/test_profile_wrapped.json
```

### 2. Analyze Job Posting
```bash
curl -X POST "http://localhost:8000/jobs/analyze" \
  -H "Content-Type: application/json" \
  -d @data/test/test_job.json
```

### 3. Generate Tailored Resume
```bash
curl -X POST "http://localhost:8000/resumes/tailor" \
  -H "Content-Type: application/json" \
  -d @data/test/test_job.json
```

## Response Formats

All responses include:
- Structured JSON data
- Error handling with clear messages
- Processing timestamps
- Session management

## Complete Documentation

- **[Quickstart Guide](../../specs/001-resume-tailoring-feature/quickstart.md)** - Complete workflow examples
- **[Live API Docs](http://localhost:8000/docs)** - Interactive Swagger UI
- **[OpenAPI Specs](../../specs/001-resume-tailoring-feature/contracts/)** - Formal API contracts