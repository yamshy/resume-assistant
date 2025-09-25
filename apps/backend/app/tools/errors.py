from __future__ import annotations


class ToolInvocationError(RuntimeError):
    """Raised when a tool cannot satisfy a request."""


__all__ = ["ToolInvocationError"]
