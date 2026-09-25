from __future__ import annotations

from abc import ABC, abstractmethod

from llm.schemas import (
    LLMMessage,
    LLMResponse,
)


class LLMProviderError(RuntimeError):
    pass


class LLMConfigurationError(
    LLMProviderError
):
    pass


class LLMProvider(ABC):
    name: str

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
