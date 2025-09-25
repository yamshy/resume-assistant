from __future__ import annotations

from datetime import timedelta
from typing import Dict, Optional

from temporalio import workflow

from ..activities import compliance, critique, drafting, ingestion, publishing
from ..state import AgentConfig, PipelineStage, ResumeWorkflowState

TASK_QUEUE = "resume-assistant"


def _initial_stage(task: Optional[str]) -> PipelineStage:
    mapping: Dict[Optional[str], PipelineStage] = {
        "ingest": "ingestion",
        "draft": "drafting",
        "revise": "drafting",
        "resume_pipeline": "ingestion",
        "compliance_only": "compliance",
        "publish": "publishing",
    }
    return mapping.get(task, "ingestion")


@workflow.defn
class ResumeWorkflow:
    """Temporal workflow orchestrating resume generation."""

    def __init__(self) -> None:
        self.state: ResumeWorkflowState | None = None
        self.config = AgentConfig()
        self._human_decision: Optional[str] = None
        self._human_notes: Optional[str] = None

    @workflow.run
    async def run(
        self,
        state: ResumeWorkflowState,
        config: Optional[AgentConfig] = None,
    ) -> ResumeWorkflowState:
        self.state = state.model_copy(deep=True)
        self.config = config or AgentConfig()
        self.state.stage = _initial_stage(self.state.task)
        self.state.status = "in_progress"
        self.state.audit_trail.append(f"workflow.bootstrap:{self.state.stage}")

        if self.state.stage == "ingestion":
            await self._run_ingestion()
            if self.state.stage == "done":
                return self.state

        if self.state.stage in {"drafting", "critique"}:
            await self._run_drafting_with_critiques()
            if self.state.stage == "done":
                return self.state

        if self.state.stage == "compliance":
            await self._run_compliance()
            if self.state.stage == "done":
                return self.state

        if self.state.stage == "publishing":
            await self._await_human_approval()
            if self.state.stage == "done":
                return self.state
            await self._run_publishing()

        self.state.stage = "done"
        if self.state.status not in {"complete", "error"}:
            self.state.status = "complete"
        self.state.audit_trail.append("workflow.completed")
        return self.state

    @workflow.signal
    def submit_human_decision(self, approved: bool, notes: Optional[str] = None) -> None:
        self._human_decision = "approved" if approved else "rejected"
        self._human_notes = notes

    @workflow.query
    def current_state(self) -> ResumeWorkflowState:
        if self.state is None:  # pragma: no cover - defensive guard
            raise RuntimeError("Workflow state not initialized")
        # Return a copy to avoid accidental mutation during replay
        return self.state.model_copy(deep=True)

    async def _run_ingestion(self) -> None:
        assert self.state is not None
        raw_documents = self.state.artifacts.get("raw_documents", {})
        normalize_result = await workflow.execute_activity(
            ingestion.normalize_documents,
            ingestion.NormalizeDocumentsInput(raw_documents=raw_documents),
            schedule_to_close_timeout=timedelta(seconds=30),
            start_to_close_timeout=timedelta(seconds=20),
            task_queue=TASK_QUEUE,
        )
        self._apply_audit(normalize_result.audit_event)
        self._merge_metrics(normalize_result.metrics)
        self.state.artifacts["normalized_documents"] = normalize_result.normalized_documents
        if normalize_result.metadata:
            self.state.artifacts["ingestion_metadata"] = normalize_result.metadata

        index_result = await workflow.execute_activity(
            ingestion.index_documents,
            ingestion.IndexDocumentsInput(
                normalized_documents=normalize_result.normalized_documents,
                request_id=self.state.request_id,
            ),
            schedule_to_close_timeout=timedelta(seconds=30),
            start_to_close_timeout=timedelta(seconds=20),
            task_queue=TASK_QUEUE,
        )
        self._apply_audit(index_result.audit_event)
        self._merge_metrics(index_result.metrics)
        self.state.artifacts["vector_index"] = index_result.vector_index
        self.state.audit_trail.append("ingestion.completed")

        if self.state.task in {"resume_pipeline", "draft", "revise"}:
            self.state.stage = "drafting"
        else:
            self.state.stage = "done"
            self.state.status = "complete"

    async def _run_drafting_with_critiques(self) -> None:
        assert self.state is not None
        revision_count = int(self.state.flags.get("revision_count", 0))
        if self.state.flags.get("skip_critique"):
            await self._run_drafting(revision_count)
            self.state.flags["needs_revision"] = False
            self.state.stage = "compliance"
            return
        while True:
            await self._run_drafting(revision_count)
            critique_result = await workflow.execute_activity(
                critique.run_critique,
                critique.CritiqueInput(
                    resume_markdown=self.state.artifacts.get("draft_resume", ""),
                    profile=self.state.artifacts.get("profile", {}),
                    revision_count=revision_count,
                    config=self.config,
                ),
                schedule_to_close_timeout=timedelta(seconds=30),
                start_to_close_timeout=timedelta(seconds=20),
                task_queue=TASK_QUEUE,
            )
            self._apply_audit(critique_result.audit_event)
            self._merge_metrics(critique_result.metrics)
            self.state.artifacts["critique"] = critique_result.critique
            self.state.flags["revision_count"] = critique_result.revision_count
            self.state.flags["needs_revision"] = critique_result.needs_revision
            if not critique_result.needs_revision:
                self.state.stage = "compliance"
                break
            revision_count = critique_result.revision_count
            self.state.audit_trail.append("drafting.revision_requested")

    async def _run_drafting(self, previous_revisions: int) -> None:
        assert self.state is not None
        plan_result = await workflow.execute_activity(
            drafting.plan_resume,
            drafting.PlanResumeInput(
                profile=self.state.artifacts.get("profile", {}),
                request_id=self.state.request_id,
                config=self.config,
            ),
            schedule_to_close_timeout=timedelta(seconds=30),
            start_to_close_timeout=timedelta(seconds=20),
            task_queue=TASK_QUEUE,
        )
        self._apply_audit(plan_result.audit_event)
        self.state.artifacts["draft_plan"] = plan_result.draft_plan
        self.state.artifacts["knowledge_hits"] = plan_result.knowledge_hits

        render_result = await workflow.execute_activity(
            drafting.render_resume,
            drafting.RenderResumeInput(
                plan=plan_result.draft_plan,
                profile=self.state.artifacts.get("profile", {}),
                knowledge_hits=plan_result.knowledge_hits,
                config=self.config,
                previous_drafts=float(self.state.metrics.get("drafts", 0.0)),
            ),
            schedule_to_close_timeout=timedelta(seconds=60),
            start_to_close_timeout=timedelta(seconds=45),
            task_queue=TASK_QUEUE,
        )
        self._apply_audit(render_result.audit_event)
        self._merge_metrics(render_result.metrics)
        self.state.artifacts["draft_resume"] = render_result.resume_markdown
        self.state.messages.append(render_result.message)
        self.state.stage = "critique"
        self.state.flags["revision_count"] = previous_revisions

    async def _run_compliance(self) -> None:
        assert self.state is not None
        compliance_result = await workflow.execute_activity(
            compliance.run_compliance_check,
            compliance.ComplianceInput(
                resume_markdown=self.state.artifacts.get("draft_resume", ""),
                profile=self.state.artifacts.get("profile", {}),
                config=self.config,
            ),
            schedule_to_close_timeout=timedelta(seconds=30),
            start_to_close_timeout=timedelta(seconds=20),
            task_queue=TASK_QUEUE,
        )
        self._apply_audit(compliance_result.audit_event)
        self.state.artifacts["compliance_report"] = compliance_result.report
        if compliance_result.status == "rejected":
            self.state.status = "error"
            self.state.stage = "done"
            return
        self.state.stage = "publishing"
        self.state.flags["awaiting_human"] = True

    async def _await_human_approval(self) -> None:
        assert self.state is not None
        self.state.audit_trail.append("publishing.awaiting_approval")
        await workflow.wait_condition(lambda: self._human_decision is not None)
        if self._human_decision == "rejected":
            self.state.status = "error"
            self.state.stage = "done"
            self.state.flags["awaiting_human"] = False
            self.state.flags["human_notes"] = self._human_notes or ""
            self.state.audit_trail.append("publishing.rejected_by_human")
        else:
            self.state.flags["awaiting_human"] = False
            self.state.audit_trail.append("publishing.approved_by_human")

    async def _run_publishing(self) -> None:
        assert self.state is not None
        persist_result = await workflow.execute_activity(
            publishing.persist_resume,
            publishing.PersistResumeInput(
                resume_markdown=self.state.artifacts.get("draft_resume", ""),
                request_id=self.state.request_id,
            ),
            schedule_to_close_timeout=timedelta(seconds=30),
            start_to_close_timeout=timedelta(seconds=20),
            task_queue=TASK_QUEUE,
        )
        self._apply_audit(persist_result.audit_event)
        self.state.artifacts["published_resume"] = persist_result.artifact

        notify_result = await workflow.execute_activity(
            publishing.notify_operations,
            publishing.NotifyInput(request_id=self.state.request_id),
            schedule_to_close_timeout=timedelta(seconds=30),
            start_to_close_timeout=timedelta(seconds=20),
            task_queue=TASK_QUEUE,
        )
        self._apply_audit(notify_result.audit_event)
        self.state.status = "complete"

    def _apply_audit(self, event: str) -> None:
        assert self.state is not None
        self.state.audit_trail.append(event)

    def _merge_metrics(self, metrics: Dict[str, float]) -> None:
        assert self.state is not None
        for key, value in metrics.items():
            self.state.metrics[key] = float(value)


__all__ = ["ResumeWorkflow", "TASK_QUEUE"]
