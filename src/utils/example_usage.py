"""
Example usage of retry utilities with pydanticAI agents.

This demonstrates how to integrate retry logic following constitutional patterns.
"""

from pydantic import BaseModel
from pydantic_ai import Agent

from .retry import configure_agent_retry, retry_agent_call


class ExampleOutput(BaseModel):
    result: str
    confidence: float


# Example agent setup
example_agent = Agent(
    "openai:gpt-4o",
    output_type=ExampleOutput,
    instructions="Example agent for demonstration purposes",
)


# Configure retry settings for this agent
retry_config = configure_agent_retry(
    agent_name="example_agent",
    max_attempts=3,  # Constitutional limit: 1-3 attempts
    timeout=5.0,  # <5 seconds per agent target
)


@retry_agent_call(retry_config)
async def run_example_agent(input_data: str) -> ExampleOutput:
    """
    Example of agent call with retry logic.

    The decorator handles:
    - Exponential backoff on failures
    - Timeout management
    - ModelRetry exception handling
    - Retry attempt limits
    """
    result = await example_agent.run(input_data)
    return result.data


# Usage in agent chain
async def example_agent_chain():
    """Example of using retry logic in an agent chain."""
    try:
        # This call will automatically retry on failures
        result = await run_example_agent("Example input")
        print(f"Success: {result.result} (confidence: {result.confidence})")
        return result
    except Exception as error:
        print(f"Agent failed after retries: {error}")
        raise
