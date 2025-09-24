from __future__ import annotations

from langchain_core.messages import HumanMessage

from app.state import DEFAULT_AUDIT_EVENT, initialize_state, summarize_state


def test_initialize_state_defaults():
    state = initialize_state(task="resume_pipeline")
    assert state["stage"] == "route"
    assert state["status"] == "pending"
    assert state["audit_trail"] == [DEFAULT_AUDIT_EVENT]
    assert state["messages"][0].content == "Resume request created."


def test_initialize_state_custom_values():
    custom_message = HumanMessage(content="Custom request")
    state = initialize_state(
        task="draft",
        messages=[custom_message],
        artifacts={"raw_documents": {"resume": "data"}},
    )
    assert state["messages"][0] is custom_message
    assert state["artifacts"]["raw_documents"]["resume"] == "data"


def test_summarize_state_returns_sorted_artifact_keys():
    state = initialize_state(task="draft", artifacts={"b": 1, "a": 2})
    summary = summarize_state(state)
    assert summary["artifacts"] == ["a", "b"]
    assert summary["task"] == "draft"
    assert summary["stage"] == "route"
