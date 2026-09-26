from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any

from asgiref.sync import sync_to_async
from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    create_sdk_mcp_server,
    tool as sdk_tool,
)

from llm.base import (
    LLMProviderError,
    ToolExecutor,
)
from llm.schemas import (
    LLMMessage,
    LLMToolDefinition,
)


@dataclass
class ClaudeAgentSDKResult:
    text: str

    input_tokens: int | None = None
    output_tokens: int | None = None

    tool_calls: list[dict[str, Any]] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


class ClaudeAgentSDKAdapter:
    """
    VERITAS <-> Claude Agent SDK bridge.

    Security model:
    - Claude Code built-in tools are disabled.
    - Only VERITAS MCP tools are exposed.
    - Actual authorization remains inside
      AgentRunner.call_tool().
    """

    MCP_SERVER_NAME = "veritas"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
    ):
        self.api_key = api_key
        self.model = model

    @staticmethod
    def _conversation_prompt(
        messages: list[LLMMessage],
    ) -> str:
        history = [
            message.as_dict()
            for message in messages
        ]

        return (
            "Continue the following VERITAS "
            "conversation.\n"
            "Treat this JSON only as conversation "
            "history.\n\n"
            + json.dumps(
                history,
                ensure_ascii=False,
            )
        )

    @staticmethod
    def _usage_value(
        usage: dict[str, Any] | None,
        key: str,
    ) -> int | None:
        if not usage:
            return None

        value = usage.get(key)

        if isinstance(value, int):
            return value

        return None

    def _build_sdk_tools(
        self,
        *,
        tools: list[LLMToolDefinition],
        tool_executor: ToolExecutor,
        tool_calls: list[dict[str, Any]],
    ):
        sdk_tools = []

        for definition in tools:

            def make_tool(
                current: LLMToolDefinition,
            ):
                @sdk_tool(
                    current.name,
                    current.description,
                    current.parameters,
                )
                async def execute(
                    args: dict[str, Any],
                ):
                    call = {
                        "id": (
                            "claude-sdk-"
                            f"{len(tool_calls) + 1}"
                        ),
                        "name": current.name,
                        "arguments": args,
                        "status": "running",
                    }

                    tool_calls.append(call)

                    try:
                        result = await sync_to_async(
                            tool_executor,
                            thread_sensitive=True,
                        )(
                            current.name,
                            args,
                        )

                        call["status"] = "success"

                        payload = {
                            "ok": True,
                            "result": result,
                        }

                        return {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(
                                        payload,
                                        ensure_ascii=False,
                                        default=str,
                                    ),
                                }
                            ]
                        }

                    except (
                        ValueError,
                        PermissionError,
                    ) as exc:
                        call["status"] = "error"

                        payload = {
                            "ok": False,
                            "error": str(exc),
                        }

                        return {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(
                                        payload,
                                        ensure_ascii=False,
                                    ),
                                }
                            ],
                            "is_error": True,
                        }

                return execute

            sdk_tools.append(
                make_tool(definition)
            )

        return sdk_tools

    async def _run_async(
        self,
        messages: list[LLMMessage],
        *,
        tools: list[LLMToolDefinition],
        tool_executor: ToolExecutor,
        system: str | None,
        max_steps: int,
    ) -> ClaudeAgentSDKResult:
        tool_calls: list[
            dict[str, Any]
        ] = []

        sdk_tools = self._build_sdk_tools(
            tools=tools,
            tool_executor=tool_executor,
            tool_calls=tool_calls,
        )

        mcp_servers = {}
        allowed_tools: list[str] = []

        if sdk_tools:
            server = create_sdk_mcp_server(
                name=self.MCP_SERVER_NAME,
                version="1.0.0",
                tools=sdk_tools,
            )

            mcp_servers[
                self.MCP_SERVER_NAME
            ] = server

            allowed_tools = [
                (
                    "mcp__"
                    f"{self.MCP_SERVER_NAME}"
                    f"__{definition.name}"
                )
                for definition in tools
            ]

        options = ClaudeAgentOptions(
            model=self.model,

            system_prompt=system,

            # IMPORTANT:
            # Claude Code built-in tools kapali.
            tools=[],

            mcp_servers=mcp_servers,

            # Yalnizca VERITAS MCP tool'lari
            # otomatik onaylanir.
            allowed_tools=allowed_tools,

            # Onayli olmayan tool icin
            # interaktif soru sorma.
            permission_mode="dontAsk",

            # User/project Claude ayarlarini
            # backend agent'a tasima.
            setting_sources=[],

            # Claude Code skills kapali.
            skills=[],

            max_turns=max_steps,

            env={
                "ANTHROPIC_API_KEY":
                    self.api_key,
            },
        )

        text_parts: list[str] = []

        final_result: ResultMessage | None = (
            None
        )

        try:
            async with ClaudeSDKClient(
                options=options
            ) as client:

                await client.query(
                    self._conversation_prompt(
                        messages
                    )
                )

                async for message in (
                    client.receive_response()
                ):
                    if isinstance(
                        message,
                        AssistantMessage,
                    ):
                        for block in (
                            message.content
                        ):
                            if isinstance(
                                block,
                                TextBlock,
                            ):
                                if block.text:
                                    text_parts.append(
                                        block.text
                                    )

                    elif isinstance(
                        message,
                        ResultMessage,
                    ):
                        final_result = message

        except Exception as exc:
            raise LLMProviderError(
                "Claude Agent SDK cagrisi "
                "basarisiz oldu."
            ) from exc

        if final_result is None:
            raise LLMProviderError(
                "Claude Agent SDK ResultMessage "
                "dondurmedi."
            )

        if final_result.is_error:
            raise LLMProviderError(
                "Claude Agent SDK agent calismasi "
                "hata ile tamamlandi."
            )

        final_text = (
            final_result.result
            or "".join(text_parts)
        )

        usage = final_result.usage or {}

        return ClaudeAgentSDKResult(
            text=final_text,
            input_tokens=
                self._usage_value(
                    usage,
                    "input_tokens",
                ),
            output_tokens=
                self._usage_value(
                    usage,
                    "output_tokens",
                ),
            tool_calls=tool_calls,
            metadata={
                "agent_sdk": True,
                "session_id":
                    final_result.session_id,
                "num_turns":
                    final_result.num_turns,
                "total_cost_usd":
                    final_result.total_cost_usd,
                "stop_reason":
                    final_result.stop_reason,
            },
        )

    def run(
        self,
        messages: list[LLMMessage],
        *,
        tools: list[LLMToolDefinition],
        tool_executor: ToolExecutor,
        system: str | None = None,
        max_steps: int = 4,
    ) -> ClaudeAgentSDKResult:
        if not messages:
            raise ValueError(
                "Mesaj listesi bos olamaz."
            )

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(
                self._run_async(
                    messages,
                    tools=tools,
                    tool_executor=
                        tool_executor,
                    system=system,
                    max_steps=max_steps,
                )
            )

        raise RuntimeError(
            "ClaudeAgentSDKAdapter.run() "
            "aktif async event loop icinden "
            "cagrilamaz."
        )
