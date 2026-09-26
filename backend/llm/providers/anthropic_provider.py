from __future__ import annotations

import json
from typing import Any

from django.conf import settings

from llm.base import (
    LLMConfigurationError,
    LLMProvider,
    LLMProviderError,
    ToolExecutor,
)
from llm.schemas import (
    LLMMessage,
    LLMResponse,
    LLMStreamEvent,
    LLMToolDefinition,
)


class AnthropicProvider(LLMProvider):
    name = "anthropic"
    supports_tools = True

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
                or settings
                .ANTHROPIC_CHAT_MODEL
            )
        )

        self.api_key = (
            settings.ANTHROPIC_API_KEY
            if api_key is None
            else api_key
        )

        self._client = client

    @property
    def configured(self) -> bool:
        return bool(
            self.api_key
            or self._client is not None
        )

    def _get_client(self):
        if self._client is not None:
            return self._client

        if not self.configured:
            raise LLMConfigurationError(
                "ANTHROPIC_API_KEY "
                "tanimli degil."
            )

        from anthropic import Anthropic

        self._client = Anthropic(
            api_key=self.api_key
        )

        return self._client

    @staticmethod
    def _usage(
        response,
    ) -> tuple[
        int | None,
        int | None,
    ]:
        usage = getattr(
            response,
            "usage",
            None,
        )

        return (
            getattr(
                usage,
                "input_tokens",
                None,
            ),
            getattr(
                usage,
                "output_tokens",
                None,
            ),
        )

    @staticmethod
    def _text(
        response,
    ) -> str:
        return "".join(
            getattr(
                block,
                "text",
                "",
            )
            for block
            in response.content
            if getattr(
                block,
                "type",
                None,
            )
            == "text"
        )

    def generate(
        self,
        messages: list[LLMMessage],
        *,
        system: str | None = None,
    ) -> LLMResponse:
        client = self._get_client()

        payload: dict[str, Any] = {
            "model": self.model,
            "max_tokens":
                settings
                .ANTHROPIC_MAX_TOKENS,
            "messages": [
                message.as_dict()
                for message in messages
            ],
        }

        if system:
            payload["system"] = system

        response = (
            client.messages.create(
                **payload
            )
        )

        (
            input_tokens,
            output_tokens,
        ) = self._usage(response)

        return LLMResponse(
            text=self._text(response),
            provider=self.name,
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=
                output_tokens,
            metadata={
                "response_id":
                    getattr(
                        response,
                        "id",
                        None,
                    ),
            },
        )


    def generate_with_tools(
        self,
        messages: list[LLMMessage],
        *,
        tools:
            list[LLMToolDefinition],
        tool_executor: ToolExecutor,
        system: str | None = None,
        max_steps: int = 4,
    ) -> LLMResponse:
        if not tools:
            return self.generate(
                messages,
                system=system,
            )

        if not self.api_key:
            raise LLMConfigurationError(
                "ANTHROPIC_API_KEY Claude "
                "Agent SDK icin tanimli degil."
            )

        # Lazy import:
        # llm -> agent -> llm circular
        # import riskini engeller.
        from agent.claude_sdk_adapter import (
            ClaudeAgentSDKAdapter,
        )

        adapter = ClaudeAgentSDKAdapter(
            api_key=self.api_key,
            model=self.model,
        )

        result = adapter.run(
            messages,
            tools=tools,
            tool_executor=tool_executor,
            system=system,
            max_steps=max_steps,
        )

        return LLMResponse(
            text=result.text,
            provider=self.name,
            model=self.model,
            input_tokens=
                result.input_tokens,
            output_tokens=
                result.output_tokens,
            tool_calls=
                result.tool_calls,
            metadata={
                **result.metadata,
                "transport":
                    "claude-agent-sdk",
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
        Claude Agent SDK native partial
        streaming.

        Text deltalari ve tool lifecycle
        eventleri geldikleri anda VERITAS
        LLMStreamEvent contract'ina map edilir.
        """

        if not self.api_key:
            raise LLMConfigurationError(
                "ANTHROPIC_API_KEY Claude "
                "Agent SDK icin tanimli degil."
            )

        from agent.claude_sdk_adapter import (
            ClaudeAgentSDKAdapter,
        )

        adapter = ClaudeAgentSDKAdapter(
            api_key=self.api_key,
            model=self.model,
        )

        for item in adapter.stream(
            messages,
            tools=tools,
            tool_executor=
                tool_executor,
            system=system,
            max_steps=
                max_steps,
        ):
            if item.type == "delta":
                if item.delta:
                    yield LLMStreamEvent(
                        type="delta",
                        delta=item.delta,
                    )

            elif (
                item.type
                == "tool_start"
            ):
                yield LLMStreamEvent(
                    type="tool_start",
                    tool_call=
                        item.tool_call
                        or {},
                )

            elif (
                item.type
                == "tool_end"
            ):
                yield LLMStreamEvent(
                    type="tool_end",
                    tool_call=
                        item.tool_call
                        or {},
                )

            elif item.type == "done":
                result = item.result

                if result is None:
                    raise LLMProviderError(
                        "Claude Agent SDK "
                        "stream sonucu yok."
                    )

                yield LLMStreamEvent(
                    type="done",
                    response=LLMResponse(
                        text=
                            result.text,
                        provider=
                            self.name,
                        model=
                            self.model,
                        input_tokens=
                            result.input_tokens,
                        output_tokens=
                            result.output_tokens,
                        tool_calls=
                            result.tool_calls,
                        metadata={
                            **result.metadata,
                            "transport":
                                "claude-agent-sdk",
                            "native_stream":
                                True,
                        },
                    ),
                )

