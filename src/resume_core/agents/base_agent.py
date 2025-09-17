from typing import Any


class Agent:
    def __init__(self, model_name: str = "gpt-4o", api_key: str | None = None):
        self.model_name = model_name
        self.api_key = api_key
        self._initialized = False

    async def initialize(self) -> None:
        if not self.api_key:
            raise ValueError("API key is required for agent initialization")
        self._initialized = True

    async def run(self, text: str) -> dict[str, Any]:
        if not self._initialized and self.api_key:
            await self.initialize()

        if not self.api_key:
            raise RuntimeError("Agent requires API key. Set OPENAI_API_KEY or mock in tests.")

        raise RuntimeError("Agent.run must be mocked in tests")
