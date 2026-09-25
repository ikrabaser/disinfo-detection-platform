from __future__ import annotations

from typing import Any

from django.conf import settings

from llm.base import (
    LLMConfigurationError,
    LLMProvider,
)
from llm.schemas import (
    LLMMessage,
    LLMResponse,
)


class OpenAIProvider(LLMProvider):
    name = "openai"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        client: Any | None = None,
    ):
        super().__init__(
            model=(
                model
                or settings.OPENAI_CHAT_MODEL
            )
        )

        self.api_key = (
            settings.OPENAI_API_KEY
            if api_key is None
            else api_key
        )

        self._client = client

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def _get_client(self):
        if self._client is not None:
            return self._client

        if not self.configured:
            raise LLMConfigurationError(
                "OPENAI_API_KEY tanimli degil."
            )

        from openai import OpenAI

        self._client = OpenAI(
            api_key=self.api_key
        )

        return self._client

    def generate(
        self,
        messages: list[LLMMessage],
        *,
        system: str | None = None,
    ) -> LLMResponse:
        client = self._get_client()

        payload: dict[str, Any] = {
            "model": self.model,
            "input": [
                message.as_dict()
                for message in messages
            ],
            "store": False,
        }

        if system:
            payload["instructions"] = system

        response = (
            client.responses.create(
                **payload
            )
        )

        usage = getattr(
            response,
            "usage",
            None,
        )

        return LLMResponse(
            text=(
                getattr(
                    response,
                    "output_text",
                    "",
                )
                or ""
            ),
            provider=self.name,
            model=self.model,
            input_tokens=getattr(
                usage,
                "input_tokens",
                None,
            ),
            output_tokens=getattr(
                usage,
                "output_tokens",
                None,
            ),
            metadata={
                "response_id": getattr(
                    response,
                    "id",
                    None,
                ),
            },
        )
