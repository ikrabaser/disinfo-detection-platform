from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable

from llm.schemas import (
    LLMMessage,
    LLMResponse,
    LLMToolDefinition,
)


ToolExecutor = Callable[
    [str, dict[str, Any]],
    Any,
]


class LLMProviderError(RuntimeError):
    pass


class LLMConfigurationError(
    LLMProviderError
):
    pass


class LLMProvider(ABC):
    name: str
    supports_tools = False

    def __init__(
        self,
        model: str,
    ):
        self.model = model

    @property
    @abstractmethod
    def configured(self) -> bool:
        """Provider kullanima hazir mi?"""

    @abstractmethod
    def generate(
        self,
        messages: list[LLMMessage],
        *,
        system: str | None = None,
    ) -> LLMResponse:
        """Tek seferlik LLM yaniti uret."""

    def generate_with_tools(
        self,
        messages: list[LLMMessage],
        *,
        tools: list[
            LLMToolDefinition
        ],
        tool_executor: ToolExecutor,
        system: str | None = None,
        max_steps: int = 4,
    ) -> LLMResponse:
        """
        Tool calling desteklemeyen provider'lar
        normal generation'a duser.
        """

        return self.generate(
            messages,
            system=system,
        )
