# Resume Assistant Data Directory

This directory contains all data files used by the Resume Assistant system.

## Directory Structure

```
data/
├── test/           # Test data for development and validation
├── real/           # Real user data (should be .gitignored in production)
├── samples/        # Sample data for documentation and examples
└── README.md       # This file
```

## Test Data (`data/test/`)

- `test_profile_wrapped.json` - Sample user profile in API format
- `test_profile.json` - Sample user profile (raw format)
- `test_job.json` - Sample job posting for testing

## Usage

```bash
# Test profile setup
curl -X PUT "http://localhost:8000/profile" \
  -H "Content-Type: application/json" \
  -d @data/test/test_profile_wrapped.json

# Test job analysis
curl -X POST "http://localhost:8000/jobs/analyze" \
  -H "Content-Type: application/json" \
  -d @data/test/test_job.json
```

## Production Data (`data/real/`)

In production, this directory will contain:
- User profile data (should be encrypted/secured)
- Session data from resume tailoring workflows
- Exported resumes
- System logs and metrics

**Note**: Real user data should never be committed to version control.