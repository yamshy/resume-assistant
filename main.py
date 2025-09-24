"""Developer-focused CLI for exercising the LangGraph supervisor locally."""

from __future__ import annotations

import json
from pprint import pprint

from app import build_default_registry, build_supervisor, initialize_state, summarize_state


def build_sample_state():
    return initialize_state(
        task="resume_pipeline",
        artifacts={
            "raw_documents": {
                "resume": "Principal engineer with deep LangGraph expertise.",
                "job": "Architect LangGraph-first systems for AI orchestration.",
            },
            "profile": {
                "name": "Sample Candidate",
                "headline": "Principal LangGraph Engineer",
                "summary": "Over a decade building production agent systems.",
                "skills": ["LangGraph", "Python", "LLM orchestration"],
                "experience": [
                    {
                        "role": "Lead Engineer",
                        "company": "Resume Assistant",
                        "impact": "Delivered the LangGraph switchover in record time.",
                    }
                ],
                "target_role": "LangGraph Engineer",
            },
        },
    )


def run_demo() -> None:
    registry = build_default_registry()
    supervisor = build_supervisor(registry=registry)
    state = build_sample_state()
    result = supervisor.invoke(state, config={"configurable": {"thread_id": state["request_id"]}})
    print("\nLangGraph run summary:")
    pprint(summarize_state(result))
    print("\nPublished resume preview:\n")
    print(result["artifacts"]["published_resume"]["content"])
    print("\nCache entry:")
    print(json.dumps(registry.cache.fetch(result["request_id"]), indent=2))
    print("\nNotifications:")
    print(json.dumps(registry.notifications.events, indent=2))


if __name__ == "__main__":
    run_demo()
