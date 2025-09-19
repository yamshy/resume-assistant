"""
File Storage Service for managing sessions and resume exports.

Handles temporary session data, final resume exports, and file operations
according to constitutional file storage patterns.

Constitutional compliance:
- File-based storage in data/ directory (local development, gitignored)
- Simple directory structure for sessions and exports
- JSON serialization for structured data
- Atomic file operations with error handling
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from models.resume_optimization import TailoredResume
from utils.validation import sanitize_filename


class StorageService:
    """
    Service for managing file storage of sessions and resume exports.

    Handles temporary session data during pipeline execution and
    final resume exports with proper file organization.
    """

    def __init__(self, base_path: str | None = None):
        """Initialize storage service with base directory."""
        if base_path:
            self.base_dir = Path(base_path)
        else:
            # Use local development storage: data/ (gitignored)
            current_dir = Path.cwd()
            self.base_dir = current_dir / "data"

        # Storage directories
        self.sessions_dir = self.base_dir / "sessions"
        self.exports_dir = self.base_dir / "exports"

        # Ensure directories exist
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)

    def _to_jsonable(self, obj: Any) -> Any:
        """Recursively convert pydantic models and other objects to JSON-serializable structures."""
        # pydantic BaseModel (v2)
        if hasattr(obj, "model_dump"):
            try:
                return obj.model_dump(mode="json")
            except Exception:
                # Fallback to plain dict
                return obj.model_dump()
        # Mapping
        if isinstance(obj, dict):
            return {k: self._to_jsonable(v) for k, v in obj.items()}
        # Iterable collections
        if isinstance(obj, (list, tuple, set)):
            return [self._to_jsonable(v) for v in obj]
        # Enum
        try:
            import enum

            if isinstance(obj, enum.Enum):
                return obj.value
        except Exception:
            pass
        # Default - assume already serializable
        return obj

    async def save_session_data(self, session_id: str, pipeline_data: dict[str, Any]) -> str:
        """
        Save complete pipeline data for a session.

        Args:
            session_id: Unique session identifier
            pipeline_data: Complete pipeline results dictionary

        Returns:
            File path where session data was saved

        Raises:
            ValueError: If saving fails
        """
        try:
            session_file = self.sessions_dir / f"{session_id}.json"

            # Convert pipeline_data to JSON-serializable form
            serializable_pipeline = self._to_jsonable(pipeline_data)

            # Add metadata
            session_data = {
                "session_id": session_id,
                "saved_at": datetime.now().isoformat(),
                "pipeline_data": serializable_pipeline,
            }

            # Write atomically using temp file
            temp_file = session_file.with_suffix(".tmp")

            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)

            # Atomic move to final location
            temp_file.replace(session_file)

            return str(session_file)

        except Exception as e:
            # Clean up temp file if it exists
            temp_file = self.sessions_dir / f"{session_id}.json.tmp"
            if temp_file.exists():
                temp_file.unlink()
            raise ValueError(f"Failed to save session data: {e}") from e

    async def load_session_data(self, session_id: str) -> dict[str, Any] | None:
        """
        Load pipeline data for a session.

        Args:
            session_id: Session identifier to load

        Returns:
            Pipeline data dictionary if found, None otherwise

        Raises:
            ValueError: If session file is corrupted
        """
        session_file = self.sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            return None

        try:
            with open(session_file, encoding="utf-8") as f:
                session_data = json.load(f)

            return session_data.get("pipeline_data")

        except json.JSONDecodeError as e:
            raise ValueError(f"Session file corrupted: {e}") from e
        except Exception as e:
            raise ValueError(f"Failed to load session: {e}") from e

    async def export_resume(
        self,
        tailored_resume: TailoredResume,
        job_title: str,
        company_name: str,
        session_id: str | None = None,
    ) -> str:
        """
        Export final resume to markdown file.

        Args:
            tailored_resume: Complete tailored resume data
            job_title: Job title for filename
            company_name: Company name for filename
            session_id: Optional session ID for tracking

        Returns:
            Path to exported resume file

        Raises:
            ValueError: If export fails
        """
        try:
            # Generate safe filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_job = sanitize_filename(job_title)
            safe_company = sanitize_filename(company_name)

            filename = f"{timestamp}_{safe_company}_{safe_job}.md"
            export_file = self.exports_dir / filename

            # Generate markdown content
            markdown_content = self._generate_markdown_resume(
                tailored_resume, job_title, company_name
            )

            # Write resume file
            with open(export_file, "w", encoding="utf-8") as f:
                f.write(markdown_content)

            # Save metadata file
            metadata = {
                "exported_at": timestamp,
                "job_title": job_title,
                "company_name": company_name,
                "session_id": session_id,
                "resume_file": filename,
                "optimizations_count": len(getattr(tailored_resume, "optimizations", [])),
            }

            metadata_file = export_file.with_suffix(".meta.json")
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            return str(export_file)

        except Exception as e:
            raise ValueError(f"Failed to export resume: {e}") from e

    async def list_exports(self) -> list[dict[str, Any]]:
        """
        List all exported resumes with metadata.

        Returns:
            List of export metadata dictionaries
        """
        exports = []

        for metadata_file in self.exports_dir.glob("*.meta.json"):
            try:
                with open(metadata_file, encoding="utf-8") as f:
                    metadata = json.load(f)

                # Check if resume file still exists
                resume_file = self.exports_dir / metadata["resume_file"]
                if resume_file.exists():
                    metadata["file_path"] = str(resume_file)
                    metadata["file_size"] = resume_file.stat().st_size
                    exports.append(metadata)

            except Exception:
                # Skip corrupted metadata files
                continue

        # Sort by export date (newest first)
        exports.sort(key=lambda x: x.get("exported_at", ""), reverse=True)
        return exports

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete session data file.

        Args:
            session_id: Session to delete

        Returns:
            True if deleted, False if not found

        Raises:
            ValueError: If deletion fails
        """
        session_file = self.sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            return False

        try:
            session_file.unlink()
            return True
        except Exception as e:
            raise ValueError(f"Failed to delete session: {e}") from e

    def _generate_markdown_resume(
        self, tailored_resume: TailoredResume, job_title: str, company_name: str
    ) -> str:
        """Generate markdown content from tailored resume."""

        # Header with generation info
        header = f"""# Resume - {job_title} at {company_name}

*Generated on {datetime.now().strftime("%B %d, %Y")}*
*Tailored with AI-powered optimization*

---

"""

        # Main resume content (use the correct field from our model)
        content = getattr(tailored_resume, "full_resume_markdown", "")

        # Optimization notes section
        optimizations_section = "\n---\n\n## Optimization Notes\n\n"
        for opt in getattr(tailored_resume, "optimizations", []):
            section_name = getattr(opt.section, "value", str(opt.section))
            reason = getattr(opt, "optimization_reason", "")
            optimizations_section += f"**{section_name}**: {reason}\n\n"

        # Estimated match score
        footer = (
            f"\n---\n\n*Estimated Job Match Score: {tailored_resume.estimated_match_score:.1%}*\n"
        )

        return header + content + optimizations_section + footer


# Factory function for service creation
def create_storage_service(base_path: str | None = None) -> StorageService:
    """
    Create a new Storage Service instance.

    Args:
        base_path: Optional custom base directory

    Returns:
        StorageService configured with specified or default path
    """
    return StorageService(base_path)


__all__ = ["StorageService", "create_storage_service"]
