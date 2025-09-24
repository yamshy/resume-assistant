from __future__ import annotations

from langgraph.graph import END, StateGraph

from ..state import AgentConfig, ResumeGraphState
from ..tools import ToolRegistry


def build_compliance_graph(registry: ToolRegistry, config: AgentConfig) -> StateGraph:
    """Compile compliance checks that guard redaction and policy adherence."""

    graph = StateGraph(ResumeGraphState)

    def run_compliance(state: ResumeGraphState) -> ResumeGraphState:
        resume_text: str = state.get("artifacts", {}).get("draft_resume", "")  # type: ignore[assignment]
        profile = state.get("artifacts", {}).get("profile", {})
        if not resume_text:
            raise ValueError("draft_resume missing before compliance checks")
        policy = {
            "blocklist": list(config.compliance_blocklist),
            "profile": profile,
        }
        review = registry.llm.compliance_review(resume_text, policy)
        status = review.get("status", "approved")
        violations = review.get("violations", [])
        if status == "rejected":
            report = {
                "status": "rejected",
                "violations": violations,
            }
            return ResumeGraphState(
                artifacts={"compliance_report": report},
                audit_trail=["compliance.rejected"],
                status="error",
                stage="done",
            )
        report = {
            "status": "approved",
            "violations": violations,
        }
        return ResumeGraphState(
            artifacts={"compliance_report": report},
            audit_trail=["compliance.approved"],
            stage="publishing",
        )

    graph.add_node("compliance", run_compliance)
    graph.set_entry_point("compliance")
    graph.add_edge("compliance", END)

    return graph


__all__ = ["build_compliance_graph"]
