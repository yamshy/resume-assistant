"""
Retry utilities for agent-chain execution.

Constitutional compliance:
- Small utility functions (<30 lines each)
- Single purpose, mechanical operations
- No complex logic - just retry mechanics
- Works with pydanticAI ModelRetry exceptions
- Performance target: <30 seconds total chain
"""

import asyncio
import random
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from pydantic_ai.exceptions import ModelRetry

T = TypeVar('T')


def exponential_backoff(attempt: int, base_delay: float = 0.5, max_delay: float = 5.0) -> float:
    """
    Calculate exponential backoff delay with jitter.

    Args:
        attempt: Current attempt number (0-based)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds

    Returns:
        Delay in seconds with jitter
    """
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = random.uniform(0.8, 1.2)  # ±20% jitter
    return delay * jitter


def should_retry(error: Exception, attempt: int, max_attempts: int = 3) -> bool:
    """
    Determine if an error should trigger a retry.

    Args:
        error: Exception that occurred
        attempt: Current attempt number (0-based)
        max_attempts: Maximum retry attempts

    Returns:
        True if should retry, False otherwise
    """
    if attempt >= max_attempts:
        return False

    # Retry on ModelRetry, network/timeout errors
    retryable_types = (ModelRetry, asyncio.TimeoutError, ConnectionError)
    return isinstance(error, retryable_types)


def configure_agent_retry(agent_name: str, max_attempts: int = 3, timeout: float = 5.0) -> dict:
    """
    Create retry configuration for a specific agent.

    Args:
        agent_name: Name of the agent
        max_attempts: Maximum retry attempts (1-3 per constitution)
        timeout: Agent timeout in seconds

    Returns:
        Retry configuration dictionary
    """
    # Constitutional limit: 1-3 retries per agent
    max_attempts = min(max(max_attempts, 1), 3)

    return {
        "agent_name": agent_name,
        "max_attempts": max_attempts,
        "timeout": timeout,
        "base_delay": 0.5,
        "max_delay": 2.0  # Keep delays short for <30s chain target
    }


async def handle_timeout(coro: Callable[[], Any], timeout: float) -> Any:
    """
    Handle timeout for async operations.

    Args:
        coro: Coroutine to execute
        timeout: Timeout in seconds

    Returns:
        Result of coroutine

    Raises:
        asyncio.TimeoutError: If operation times out
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except TimeoutError as err:
        raise TimeoutError(f"Operation timed out after {timeout}s") from err


def retry_agent_call(config: dict):
    """
    Decorator for agent calls with retry logic.

    Args:
        config: Retry configuration from configure_agent_retry()

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_error = None

            for attempt in range(config["max_attempts"]):
                try:
                    # Apply timeout wrapper
                    coro = func(*args, **kwargs)
                    return await handle_timeout(coro, config["timeout"])

                except Exception as error:
                    last_error = error

                    if not should_retry(error, attempt, config["max_attempts"]):
                        raise error

                    if attempt < config["max_attempts"] - 1:  # Don't delay on last attempt
                        delay = exponential_backoff(
                            attempt,
                            config["base_delay"],
                            config["max_delay"]
                        )
                        await asyncio.sleep(delay)

            # All retries exhausted
            raise last_error

        return wrapper
    return decorator


class RetryMetrics:
    """Simple retry metrics tracking."""

    def __init__(self):
        self.retry_counts = {}
        self.success_after_retry = {}
        self.total_retry_time = {}

    def record_retry(self, agent_name: str, attempt: int, delay: float) -> None:
        """Record a retry attempt."""
        if agent_name not in self.retry_counts:
            self.retry_counts[agent_name] = 0
            self.total_retry_time[agent_name] = 0.0

        self.retry_counts[agent_name] += 1
        self.total_retry_time[agent_name] += delay

    def record_success(self, agent_name: str, final_attempt: int) -> None:
        """Record successful completion after retries."""
        if final_attempt > 0:
            self.success_after_retry[agent_name] = final_attempt

    def get_stats(self) -> dict:
        """Get retry statistics."""
        return {
            "retry_counts": self.retry_counts.copy(),
            "success_after_retry": self.success_after_retry.copy(),
            "total_retry_time": self.total_retry_time.copy()
        }


# Global metrics instance for tracking
retry_metrics = RetryMetrics()
