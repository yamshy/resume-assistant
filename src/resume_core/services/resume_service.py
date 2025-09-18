from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any
from uuid import UUID
from zipfile import ZIP_DEFLATED, ZipFile

from xml.sax.saxutils import escape

from resume_core.agents.human_interface_agent import HumanInterfaceAgent
from resume_core.agents.job_analysis_agent import JobAnalysisAgent
from resume_core.agents.profile_matching_agent import ProfileMatchingAgent
from resume_core.agents.resume_generation_agent import ResumeGenerationAgent
from resume_core.agents.validation_agent import ValidationAgent
from resume_core.models import (
    ApprovalDecision,
    ApprovalOutcome,
    ApprovalWorkflow,
    ResumeHistoryItem,
    TailoringRecord,
    TailoringResult,
    UserProfile,
)
from resume_core.models.matching import MatchingResult
from resume_core.models.validation import ValidationResult
from .profile_service import ProfileService
from .storage_service import StorageService


@dataclass
class ResumeDownloadPayload:
    content: bytes
    media_type: str
    filename: str


class ResumeService:
    def __init__(
        self,
        profile_service: ProfileService,
        storage_service: StorageService,
        resumes_dir: Path | None = None,
        job_analysis_agent: JobAnalysisAgent | None = None,
        profile_matching_agent: ProfileMatchingAgent | None = None,
        resume_generation_agent: ResumeGenerationAgent | None = None,
        validation_agent: ValidationAgent | None = None,
        human_interface_agent: HumanInterfaceAgent | None = None,
    ) -> None:
        self.profile_service = profile_service
        self.storage = storage_service
        self.resumes_dir = self._determine_resumes_dir(resumes_dir)
        self.job_analysis_agent = job_analysis_agent or JobAnalysisAgent()
        self.profile_matching_agent = profile_matching_agent or ProfileMatchingAgent()
        self.resume_generation_agent = resume_generation_agent or ResumeGenerationAgent()
        self.validation_agent = validation_agent or ValidationAgent()
        self.human_interface_agent = human_interface_agent or HumanInterfaceAgent()

    async def tailor_resume(
        self,
        job_description: str,
        preferences: dict[str, Any] | None = None,
    ) -> TailoringResult:
        profile = await self._require_profile()
        analysis = await self.job_analysis_agent.analyze(job_description)
        matching = await self.profile_matching_agent.match(profile, analysis)
        if preferences and preferences.get("emphasis_areas"):
            emphasis = ", ".join(preferences["emphasis_areas"])
            matching.recommendations.append(f"Emphasize emphasis areas: {emphasis}")
        resume = await self.resume_generation_agent.generate(profile, analysis, matching)
        validation = await self.validation_agent.validate(profile, analysis, matching, resume)
        workflow = self._build_workflow(matching, validation)

        record = TailoringRecord.create(
            job_analysis=analysis,
            matching_result=matching,
            tailored_resume=resume,
            validation_result=validation,
            approval_workflow=workflow,
        )
        await self._persist_record(record)
        return record.to_result()

    async def get_resume(self, resume_id: str) -> TailoringRecord | None:
        normalized_id = self._normalize_resume_id(resume_id)
        record_path = self.resumes_dir / f"{normalized_id}.json"
        try:
            data = await self.storage.read_json(record_path)
        except ValueError as exc:
            raise FileNotFoundError("Resume not found") from exc
        if data is None:
            return None
        return TailoringRecord.model_validate(data)

    async def approve_resume(
        self,
        resume_id: str,
        decision: str,
        feedback: str | None = None,
        reviewer: str | None = None,
        approved_sections: list[str] | None = None,
        rejected_sections: list[str] | None = None,
    ) -> ApprovalOutcome:
        record = await self.get_resume(resume_id)
        if record is None:
            raise FileNotFoundError("Resume not found")

        approval_decision: ApprovalDecision = await self.human_interface_agent.review(
            record.tailored_resume,
            decision=decision,
            feedback=feedback,
            reviewer=reviewer,
            approved_sections=approved_sections,
            rejected_sections=rejected_sections,
        )
        record.apply_decision(approval_decision)
        await self._persist_record(record)
        download_url = f"/resumes/{record.resume_id}/download?format=markdown"
        return record.approval_outcome(download_url)

    async def download_resume(self, resume_id: str, format: str) -> ResumeDownloadPayload:
        normalized_id = self._normalize_resume_id(resume_id)
        record = await self.get_resume(normalized_id)
        if record is None:
            raise FileNotFoundError("Resume not found")

        markdown = record.tailored_resume.full_resume_markdown
        if format == "markdown":
            return ResumeDownloadPayload(
                content=markdown.encode("utf-8"),
                media_type="text/markdown; charset=utf-8",
                filename=f"{normalized_id}.md",
            )
        if format == "pdf":
            pdf_bytes = self._render_pdf(markdown)
            return ResumeDownloadPayload(
                content=pdf_bytes,
                media_type="application/pdf",
                filename=f"{normalized_id}.pdf",
            )
        if format == "docx":
            docx_bytes = self._render_docx(markdown)
            return ResumeDownloadPayload(
                content=docx_bytes,
                media_type=(
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                ),
                filename=f"{normalized_id}.docx",
            )
        raise ValueError(f"Unsupported format requested: {format}")

    async def list_resumes(self) -> list[TailoringRecord]:
        files = await self.storage.list_files(self.resumes_dir)
        records: list[TailoringRecord] = []
        for file in files:
            if file.suffix != ".json":
                continue
            try:
                relative = file.relative_to(self.storage.base_path)
                data = await self.storage.read_json(relative)
            except ValueError:
                continue
            if data is None:
                continue
            record = TailoringRecord.model_validate(data)
            records.append(record)
        records.sort(
            key=lambda record: record.tailored_resume.generation_timestamp,
            reverse=True,
        )
        return records

    async def get_history(
        self, limit: int, offset: int
    ) -> tuple[list[ResumeHistoryItem], int]:
        records = await self.list_resumes()
        total = len(records)
        if offset >= total:
            return [], total
        sliced = records[offset : offset + limit]
        return [record.to_history_item() for record in sliced], total

    async def _persist_record(self, record: TailoringRecord) -> None:
        json_path = self.resumes_dir / f"{record.resume_id}.json"
        markdown_path = self.resumes_dir / f"{record.resume_id}.md"
        await self.storage.write_json(json_path, record.model_dump(mode="json"))
        await self.storage.write_text(markdown_path, record.tailored_resume.full_resume_markdown)

    async def _require_profile(self) -> UserProfile:
        profile = await self.profile_service.load_profile()
        if profile is None:
            raise FileNotFoundError("Profile not found")
        return profile

    def _determine_resumes_dir(self, resumes_dir: Path | None) -> Path:
        requested = Path(resumes_dir) if resumes_dir is not None else Path("resumes")
        if requested.is_absolute():
            try:
                return requested.relative_to(self.storage.base_path)
            except ValueError as exc:
                raise ValueError(
                    "Resume storage directory must be inside the configured storage base"
                ) from exc
        return requested

    def _normalize_resume_id(self, resume_id: str | UUID) -> str:
        try:
            return str(UUID(str(resume_id)))
        except ValueError as exc:
            raise FileNotFoundError("Resume not found") from exc

    def _build_workflow(
        self, matching: MatchingResult, validation: ValidationResult
    ) -> ApprovalWorkflow:
        requires_review = validation.is_valid is False or matching.overall_match_score < 0.85
        confidence = min(1.0, 0.75 + matching.overall_match_score / 4)
        return ApprovalWorkflow(
            requires_human_review=requires_review,
            review_reasons=(
                ["Match score below 0.85"] if requires_review and matching.overall_match_score < 0.85 else []
            ),
            confidence_score=round(confidence, 2),
            auto_approve_eligible=not requires_review
            and validation.is_valid
            and matching.overall_match_score >= 0.9,
        )

    def _markdown_to_plain_text(self, markdown: str) -> str:
        plain_lines: list[str] = []
        for line in markdown.splitlines():
            stripped = line.lstrip("# ").strip()
            plain_lines.append(stripped)
        plain_text = "\n".join(filter(None, plain_lines)).strip()
        return plain_text or "Tailored Resume"

    def _render_pdf(self, markdown: str) -> bytes:
        text = self._markdown_to_plain_text(markdown)
        escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        content_stream = f"BT /F1 11 Tf 72 720 Td ({escaped[:1000]}) Tj ET"
        pdf_parts = [
            "%PDF-1.4",
            "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj",
            "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj",
            "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj",
            f"4 0 obj << /Length {len(content_stream)} >> stream",
            content_stream,
            "endstream endobj",
            "5 0 obj << /Type /Font /Subtype /Type1 /Name /F1 /BaseFont /Helvetica >> endobj",
            "xref",
            "0 6",
            "0000000000 65535 f ",
            "0000000010 00000 n ",
            "0000000060 00000 n ",
            "0000000111 00000 n ",
            "0000000224 00000 n ",
            "0000000345 00000 n ",
            "trailer << /Size 6 /Root 1 0 R >>",
            "startxref",
            "460",
            "%%EOF",
        ]
        return "\n".join(pdf_parts).encode("utf-8")

    def _render_docx(self, markdown: str) -> bytes:
        text = self._markdown_to_plain_text(markdown)
        lines = text.splitlines() or [text]
        document_xml_lines = [
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>",
            "<w:document xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\">",
            "  <w:body>",
        ]
        for line in lines:
            document_xml_lines.append(
                "    <w:p><w:r><w:t>%s</w:t></w:r></w:p>" % escape(line)
            )
        document_xml_lines.extend(["  </w:body>", "</w:document>"])
        document_xml = "\n".join(document_xml_lines)

        content_types_xml = """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<Types xmlns=\"http://schemas.openxmlformats.org/package/2006/content-types\">
  <Default Extension=\"rels\" ContentType=\"application/vnd.openxmlformats-package.relationships+xml\"/>
  <Default Extension=\"xml\" ContentType=\"application/xml\"/>
  <Override PartName=\"/word/document.xml\" ContentType=\"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml\"/>
</Types>
"""

        rels_xml = """<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>
<Relationships xmlns=\"http://schemas.openxmlformats.org/package/2006/relationships\">
  <Relationship Id=\"rId1\" Type=\"http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument\" Target=\"word/document.xml\"/>
</Relationships>
"""

        buffer = BytesIO()
        with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as archive:
            archive.writestr("[Content_Types].xml", content_types_xml)
            archive.writestr("_rels/.rels", rels_xml)
            archive.writestr("word/document.xml", document_xml)
        return buffer.getvalue()
