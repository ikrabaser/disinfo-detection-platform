from __future__ import annotations

from typing import Any

from django.conf import settings

from llm.base import (
    LLMConfigurationError,
    LLMProvider,
    ToolExecutor,
)
from llm.schemas import (
    LLMMessage,
    LLMResponse,
    LLMStreamEvent,
    LLMToolDefinition,
)


class EvrenProvider(LLMProvider):
    name = "evren"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        client: Any | None = None,
    ):
        super().__init__(
            model=(
                model
                or settings.EVREN_CHAT_MODEL
            )
        )

        self.api_key = (
            settings.EVREN_API_KEY
            if api_key is None
            else api_key
        )

        self.base_url = (
            settings.EVREN_BASE_URL
            if base_url is None
            else base_url
        )

        self._client = client

    @property
    def configured(self) -> bool:
        return bool(
            self.api_key
            and self.base_url
            and self.model
        )

    def _get_client(self):
        if self._client is not None:
            return self._client

        if not self.configured:
            raise LLMConfigurationError(
                "EVREN_API_KEY, "
                "EVREN_BASE_URL veya "
                "EVREN_CHAT_MODEL tanimli degil."
            )

        from openai import OpenAI

        self._client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            default_headers={
                "X-API-Key": self.api_key,
            },
        )

        return self._client

    def generate(
        self,
        messages: list[LLMMessage],
        *,
        system: str | None = None,
    ) -> LLMResponse:
        client = self._get_client()

        api_messages = []

        if system:
            api_messages.append(
                {
                    "role": "system",
                    "content": system,
                }
            )

        api_messages.extend(
            message.as_dict()
            for message in messages
        )

        response = (
            client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                reasoning_effort=(
                    settings
                    .EVREN_REASONING_EFFORT
                ),
            )
        )

        message = (
            response.choices[0].message
        )

        usage = getattr(
            response,
            "usage",
            None,
        )

        return LLMResponse(
            text=(
                getattr(
                    message,
                    "content",
                    "",
                )
                or ""
            ),
            provider=self.name,
            model=self.model,
            input_tokens=getattr(
                usage,
                "prompt_tokens",
                None,
            ),
            output_tokens=getattr(
                usage,
                "completion_tokens",
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

    def stream_with_tools(
        self,
        messages: list[LLMMessage],
        *,
        tools:
            list[LLMToolDefinition],
        tool_executor: ToolExecutor,
        system: str | None = None,
        max_steps: int = 4,
    ):
        """
        EVREN OpenAI-compatible native stream.

        EVREN su anda VERITAS tool calling
        desteklemiyor; tools/tool_executor
        contract uyumlulugu icin alinir.
        """

        del tools
        del tool_executor
        del max_steps

        client = self._get_client()

        api_messages = []

        if system:
            api_messages.append(
                {
                    "role": "system",
                    "content": system,
                }
            )

        api_messages.extend(
            message.as_dict()
            for message in messages
        )

        stream = (
            client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                reasoning_effort=(
                    settings
                    .EVREN_REASONING_EFFORT
                ),
                stream=True,
            )
        )

        text_parts: list[str] = []

        response_id = None
        input_tokens = None
        output_tokens = None

        for chunk in stream:
            if response_id is None:
                response_id = getattr(
                    chunk,
                    "id",
                    None,
                )

            usage = getattr(
                chunk,
                "usage",
                None,
            )

            if usage is not None:
                input_tokens = getattr(
                    usage,
                    "prompt_tokens",
                    input_tokens,
                )

                output_tokens = getattr(
                    usage,
                    "completion_tokens",
                    output_tokens,
                )

            choices = (
                getattr(
                    chunk,
                    "choices",
                    None,
                )
                or []
            )

            if not choices:
                continue

            delta = getattr(
                choices[0],
                "delta",
                None,
            )

            content = (
                getattr(
                    delta,
                    "content",
                    "",
                )
                if delta is not None
                else ""
            )

            if not isinstance(
                content,
                str,
            ):
                continue

            if not content:
                continue

            text_parts.append(
                content
            )

            yield LLMStreamEvent(
                type="delta",
                delta=content,
            )

        yield LLMStreamEvent(
            type="done",
            response=LLMResponse(
                text="".join(
                    text_parts
                ),
                provider=self.name,
                model=self.model,
                input_tokens=
                    input_tokens,
                output_tokens=
                    output_tokens,
                metadata={
                    "response_id":
                        response_id,
                    "transport":
                        "evren-native-stream",
                },
            ),
        )
