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


class OpenAIProvider(LLMProvider):
    name = "openai"
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
        return bool(
            self.api_key
            or self._client is not None
        )

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
            payload[
                "instructions"
            ] = system

        response = (
            client.responses.create(
                **payload
            )
        )

        (
            input_tokens,
            output_tokens,
        ) = self._usage(response)

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

        api_input: list[Any] = [
            message.as_dict()
            for message in messages
        ]

        api_tools = [
            {
                "type": "function",
                "name": tool.name,
                "description":
                    tool.description,
                "parameters":
                    tool.parameters,
                # Arguments are still
                # validated by Python.
                "strict": False,
            }
            for tool in tools
        ]

        tool_calls: list[
            dict[str, Any]
        ] = []

        total_input = 0
        total_output = 0

        last_response = None

        for _ in range(max_steps):
            payload: dict[
                str,
                Any,
            ] = {
                "model": self.model,
                "input": api_input,
                "tools": api_tools,
                "tool_choice": "auto",
                "store": False,
            }

            if system:
                payload[
                    "instructions"
                ] = system

            response = (
                client.responses.create(
                    **payload
                )
            )

            last_response = response

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
                item
                for item in getattr(
                    response,
                    "output",
                    [],
                )
                if getattr(
                    item,
                    "type",
                    None,
                )
                == "function_call"
            ]

            if not calls:
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

            # OpenAI'nin uretdigi
            # function_call item'larini
            # sonraki turn'e geri ver.
            api_input.extend(
                response.output
            )

            for call in calls:
                call_id = str(
                    getattr(
                        call,
                        "call_id",
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

                raw_arguments = (
                    getattr(
                        call,
                        "arguments",
                        "{}",
                    )
                    or "{}"
                )

                status = "success"

                try:
                    arguments = (
                        json.loads(
                            raw_arguments
                        )
                    )

                    if not isinstance(
                        arguments,
                        dict,
                    ):
                        raise ValueError(
                            "Tool arguments "
                            "JSON object olmali."
                        )

                    result = (
                        tool_executor(
                            name,
                            arguments,
                        )
                    )

                    output = json.dumps(
                        {
                            "ok": True,
                            "result": result,
                        },
                        ensure_ascii=False,
                        default=str,
                    )

                except (
                    ValueError,
                    PermissionError,
                ) as exc:
                    status = "error"

                    output = json.dumps(
                        {
                            "ok": False,
                            "error":
                                str(exc),
                        },
                        ensure_ascii=False,
                    )

                except Exception:
                    status = "error"

                    output = json.dumps(
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

                api_input.append(
                    {
                        "type":
                            "function_call_output",
                        "call_id":
                            call_id,
                        "output":
                            output,
                    }
                )

        raise LLMProviderError(
            "OpenAI tool-call dongusu "
            f"{max_steps} adimi asti."
        )
