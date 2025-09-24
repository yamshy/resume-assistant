from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Protocol

from .cache import PublishingCacheTool
from .errors import ToolInvocationError
from .llm import OpenAIResumeLLM, ResumeLLM
from .notifications import NotificationTool
from .render import ResumeRendererTool
from .vector import VectorSearchTool


class Tool(Protocol):
    name: str
    description: str


@dataclass(slots=True)
class ToolRegistry:
    """Container that exposes opinionated tool accessors for graphs."""

    vector_store: VectorSearchTool
    renderer: ResumeRendererTool
    cache: PublishingCacheTool
    notifications: NotificationTool
    llm: ResumeLLM

    def as_dict(self) -> Dict[str, Tool]:
        return {
            "vector_store": self.vector_store,
            "renderer": self.renderer,
            "cache": self.cache,
            "notifications": self.notifications,
        }


def build_default_registry() -> ToolRegistry:
    return ToolRegistry(
        vector_store=VectorSearchTool(),
        renderer=ResumeRendererTool(),
        cache=PublishingCacheTool(),
        notifications=NotificationTool(),
        llm=OpenAIResumeLLM(),
    )


__all__ = [
    "Tool",
    "NotificationTool",
    "PublishingCacheTool",
    "ResumeRendererTool",
    "VectorSearchTool",
    "ToolInvocationError",
    "ToolRegistry",
    "build_default_registry",
    "OpenAIResumeLLM",
    "ResumeLLM",
]
