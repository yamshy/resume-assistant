"""Utility helpers shared across the service."""

from __future__ import annotations

import math
from typing import Iterable, Sequence


def cosine_similarity(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
    """Compute cosine similarity between two vectors.

    The implementation avoids pulling in heavy numerical dependencies.  Inputs are
    coerced to floats and missing values default to zero.  If either vector has
    zero magnitude, the similarity defaults to ``0.0``.
    """

    a = [float(value) for value in vec_a]
    b = [float(value) for value in vec_b]

    if len(a) != len(b):
        length = max(len(a), len(b))
        a = a + [0.0] * (length - len(a))
        b = b + [0.0] * (length - len(b))

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot / (norm_a * norm_b)


def sliding_window(iterable: Sequence[str], size: int) -> Iterable[str]:
    """Yield concatenated sliding windows of text for context comparisons."""

    if size <= 0:
        raise ValueError("size must be positive")

    for index in range(len(iterable)):
        window = iterable[index : index + size]
        if len(window) < size:
            break
        yield " ".join(window)
