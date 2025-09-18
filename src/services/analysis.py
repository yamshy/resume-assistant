from typing import Any

from agents import Agent


class AnalysisService:
    def __init__(self, agent: Agent | None = None):
        self.agent = agent or Agent()

    async def analyze(self, text: str) -> dict[str, Any]:
        if not text or not text.strip():
            return {"error": "Empty input provided"}

        try:
            result = await self.agent.run(text)
            return {"status": "success", "result": result}
        except RuntimeError as e:
            if "mock" in str(e).lower():
                return {"status": "mock_required", "input": text}
            raise
        except Exception as e:
            return {"status": "error", "error": str(e)}
