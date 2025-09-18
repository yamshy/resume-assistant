"""
Resume Assistant API package.

Contains all FastAPI route handlers organized by functionality:
- health: Health check endpoints
- profile: User profile management
- jobs: Job posting analysis
- resumes: Resume tailoring pipeline
- approval: Human approval workflow
- download: Resume export and download
- history: Resume history and metadata
"""

__all__ = ["health", "profile", "jobs", "resumes", "approval", "download", "history"]
