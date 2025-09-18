from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from pydantic_ai import Agent as PydanticAgent
from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.function import FunctionModel


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


OutputT = TypeVar("OutputT", bound=BaseModel)


class FunctionBackedAgent(Generic[OutputT], ABC):
    def __init__(self, *, name: str, instructions: str, output_model: type[OutputT]):
        self._output_model = output_model
        self._agent = PydanticAgent(
            FunctionModel(function=self._function),
            instructions=instructions,
            name=name,
        )

    async def run(self, payload: Any) -> OutputT:
        input_text = self._prepare_input_text(payload)
        result = await self._agent.run(input_text)
        return self._output_model.model_validate_json(result.output)

    def _function(self, messages: list[Any], agent_info: Any) -> ModelResponse:
        payload = self._extract_payload(messages)
        output_model = self.build_output(payload)
        return ModelResponse(parts=[TextPart(content=output_model.model_dump_json())])

    def _extract_payload(self, messages: list[Any]) -> dict[str, Any]:
        for message in reversed(messages):
            if isinstance(message, ModelRequest):
                for part in message.parts:
                    if isinstance(part, UserPromptPart):
                        content = part.content
                        if isinstance(content, str):
                            return self._parse_content(content)
                        if isinstance(content, list) and content:
                            combined = " ".join(str(item) for item in content)
                            return self._parse_content(combined)
        return {}

    @staticmethod
    def _prepare_input_text(payload: Any) -> str:
        if isinstance(payload, BaseModel):
            return payload.model_dump_json()
        if isinstance(payload, str):
            return payload
        if isinstance(payload, bytes):
            return payload.decode()
        return json.dumps(payload, default=FunctionBackedAgent._json_default)

    @staticmethod
    def _parse_content(content: str) -> dict[str, Any]:
        text = content.strip()
        if not text:
            return {}
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"text": text}

    @abstractmethod
    def build_output(self, payload: dict[str, Any]) -> OutputT:
        raise NotImplementedError

    @staticmethod
    def _json_default(value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, BaseModel):
            return value.model_dump()
        raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")
