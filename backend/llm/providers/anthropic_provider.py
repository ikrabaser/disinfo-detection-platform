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

        client = self._get_client()

        api_messages: list[
            dict[str, Any]
        ] = [
            message.as_dict()
            for message in messages
        ]

        api_tools = [
            {
                "name": tool.name,
                "description":
                    tool.description,
                "input_schema":
                    tool.parameters,
            }
            for tool in tools
        ]

        tool_calls: list[
            dict[str, Any]
        ] = []

        total_input = 0
        total_output = 0

        for _ in range(max_steps):
            payload: dict[
                str,
                Any,
            ] = {
                "model": self.model,
                "max_tokens":
                    settings
                    .ANTHROPIC_MAX_TOKENS,
                "messages":
                    api_messages,
                "tools":
                    api_tools,
            }

            if system:
                payload["system"] = (
                    system
                )

            response = (
                client.messages.create(
                    **payload
                )
            )

            (
                input_tokens,
                output_tokens,
            ) = self._usage(response)

            total_input += (
                input_tokens or 0
            )

            total_output += (
                output_tokens or 0
            )

            calls = [
                block
                for block
                in response.content
                if getattr(
                    block,
                    "type",
                    None,
                )
                == "tool_use"
            ]

            if not calls:
                return LLMResponse(
                    text=self._text(
                        response
                    ),
                    provider=self.name,
                    model=self.model,
                    input_tokens=
                        total_input,
                    output_tokens=
                        total_output,
                    tool_calls=
                        tool_calls,
                    metadata={
                        "response_id":
                            getattr(
                                response,
                                "id",
                                None,
                            ),
                    },
                )

            api_messages.append(
                {
                    "role":
                        "assistant",
                    "content":
                        response.content,
                }
            )

            results = []

            for call in calls:
                call_id = str(
                    getattr(
                        call,
                        "id",
                        "",
                    )
                )

                name = str(
                    getattr(
                        call,
                        "name",
                        "",
                    )
                )

                arguments = (
                    getattr(
                        call,
                        "input",
                        {},
                    )
                    or {}
                )

                status = "success"

                try:
                    if not isinstance(
                        arguments,
                        dict,
                    ):
                        raise ValueError(
                            "Tool arguments "
                            "object olmali."
                        )

                    result = (
                        tool_executor(
                            name,
                            arguments,
                        )
                    )

                    content = (
                        json.dumps(
                            {
                                "ok": True,
                                "result":
                                    result,
                            },
                            ensure_ascii=False,
                            default=str,
                        )
                    )

                    is_error = False

                except (
                    ValueError,
                    PermissionError,
                ) as exc:
                    status = "error"
                    is_error = True

                    content = json.dumps(
                        {
                            "ok": False,
                            "error":
                                str(exc),
                        },
                        ensure_ascii=False,
                    )

                except Exception:
                    status = "error"
                    is_error = True

                    content = json.dumps(
                        {
                            "ok": False,
                            "error":
                                "Tool execution failed.",
                        }
                    )

                tool_calls.append(
                    {
                        "id": call_id,
                        "name": name,
                        "status": status,
                    }
                )

                results.append(
                    {
                        "type":
                            "tool_result",
                        "tool_use_id":
                            call_id,
                        "content":
                            content,
                        "is_error":
                            is_error,
                    }
                )

            # Anthropic tool_result
            # kullanici mesajinda ve
            # tool_use'dan hemen sonra
            # gonderilmelidir.
            api_messages.append(
                {
                    "role": "user",
                    "content": results,
                }
            )

        raise LLMProviderError(
            "Anthropic tool-call dongusu "
            f"{max_steps} adimi asti."
        )
