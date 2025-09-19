"""Prompt templates used by agents."""

from .ingestion import INGESTION_PROMPT
from .generation import GENERATION_PROMPT
from .validation import VALIDATION_PROMPT

__all__ = ["INGESTION_PROMPT", "GENERATION_PROMPT", "VALIDATION_PROMPT"]
