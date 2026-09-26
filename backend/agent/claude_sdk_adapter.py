from __future__ import annotations

import asyncio
import json
import sys
import queue
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

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
from claude_agent_sdk.types import (
    StreamEvent,
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

    tool_calls: list[
        dict[str, Any]
    ] = field(
        default_factory=list
    )

    metadata: dict[
        str,
        Any,
    ] = field(
        default_factory=dict
    )


@dataclass(slots=True)
class ClaudeAgentSDKStreamItem:
    type: Literal[
        "delta",
        "tool_start",
        "tool_end",
        "done",
    ]

    delta: str = ""

    tool_call: (
        dict[str, Any]
        | None
    ) = None

    result: (
        ClaudeAgentSDKResult
        | None
    ) = None


StreamSink = Callable[
    [ClaudeAgentSDKStreamItem],
    None,
]


def _run_sdk_coroutine(
    coroutine,
):
    """
    Claude Agent SDK Claude CLI'yi bir
    subprocess olarak baslatir.

    Windows worker context'lerinde Selector
    event loop subprocess transport
    desteklemedigi icin explicit Proactor
    loop kullanilir.
    """

    if (
        sys.platform
        != "win32"
    ):
        return asyncio.run(
            coroutine
        )

    proactor_loop_class = getattr(
        asyncio,
        "ProactorEventLoop",
        None,
    )

    if proactor_loop_class is None:
        return asyncio.run(
            coroutine
        )

    loop = proactor_loop_class()

    try:
        asyncio.set_event_loop(
            loop
        )

        return loop.run_until_complete(
            coroutine
        )

    finally:
        try:
            loop.run_until_complete(
                loop.shutdown_asyncgens()
            )
        finally:
            asyncio.set_event_loop(
                None
            )
            loop.close()


class ClaudeAgentSDKAdapter:
    """
    VERITAS <-> Claude Agent SDK bridge.

    Security model:
    - Claude Code built-in tools are disabled.
    - Only VERITAS MCP tools are exposed.
    - Authorization remains inside
      AgentRunner.call_tool().
    - Thinking/reasoning content is never
      forwarded to the frontend.
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
        usage: dict[
            str,
            Any,
        ]
        | None,
        key: str,
    ) -> int | None:
        if not usage:
            return None

        value = usage.get(
            key
        )

        if isinstance(
            value,
            int,
        ):
            return value

        return None

    def _build_sdk_tools(
        self,
        *,
        tools: list[
            LLMToolDefinition
        ],
        tool_executor:
            ToolExecutor,
        tool_calls: list[
            dict[str, Any]
        ],
        event_sink:
            StreamSink
            | None = None,
    ):
        sdk_tools = []

        for definition in tools:

            def make_tool(
                current:
                    LLMToolDefinition,
            ):
                @sdk_tool(
                    current.name,
                    current.description,
                    current.parameters,
                )
                async def execute(
                    args: dict[
                        str,
                        Any,
                    ],
                ):
                    call = {
                        "id": (
                            "claude-sdk-"
                            f"{len(tool_calls) + 1}"
                        ),
                        "name":
                            current.name,
                        "arguments":
                            args,
                        "status":
                            "running",
                    }

                    tool_calls.append(
                        call
                    )

                    if (
                        event_sink
                        is not None
                    ):
                        event_sink(
                            ClaudeAgentSDKStreamItem(
                                type=
                                    "tool_start",
                                tool_call={
                                    "id":
                                        call["id"],
                                    "name":
                                        current.name,
                                },
                            )
                        )

                    is_error = False

                    try:
                        result = (
                            await sync_to_async(
                                tool_executor,
                                thread_sensitive=True,
                            )(
                                current.name,
                                args,
                            )
                        )

                        call["status"] = (
                            "success"
                        )

                        payload = {
                            "ok": True,
                            "result": result,
                        }

                    except (
                        ValueError,
                        PermissionError,
                    ) as exc:
                        is_error = True

                        call["status"] = (
                            "error"
                        )

                        payload = {
                            "ok": False,
                            "error":
                                str(exc),
                        }

                    except Exception:
                        is_error = True

                        call["status"] = (
                            "error"
                        )

                        payload = {
                            "ok": False,
                            "error": (
                                "Tool execution "
                                "failed."
                            ),
                        }

                    if (
                        event_sink
                        is not None
                    ):
                        event_sink(
                            ClaudeAgentSDKStreamItem(
                                type=
                                    "tool_end",
                                tool_call={
                                    "id":
                                        call["id"],
                                    "name":
                                        current.name,
                                    "status":
                                        call[
                                            "status"
                                        ],
                                },
                            )
                        )

                    response = {
                        "content": [
                            {
                                "type":
                                    "text",
                                "text":
                                    json.dumps(
                                        payload,
                                        ensure_ascii=False,
                                        default=str,
                                    ),
                            }
                        ]
                    }

                    if is_error:
                        response[
                            "is_error"
                        ] = True

                    return response

                return execute

            sdk_tools.append(
                make_tool(
                    definition
                )
            )

        return sdk_tools

    async def _run_async(
        self,
        messages: list[
            LLMMessage
        ],
        *,
        tools: list[
            LLMToolDefinition
        ],
        tool_executor:
            ToolExecutor,
        system: str | None,
        max_steps: int,
        partial_messages:
            bool = False,
        event_sink:
            StreamSink
            | None = None,
    ) -> ClaudeAgentSDKResult:
        tool_calls: list[
            dict[str, Any]
        ] = []

        sdk_tools = (
            self._build_sdk_tools(
                tools=tools,
                tool_executor=
                    tool_executor,
                tool_calls=
                    tool_calls,
                event_sink=
                    event_sink,
            )
        )

        mcp_servers = {}

        allowed_tools: list[
            str
        ] = []

        if sdk_tools:
            server = (
                create_sdk_mcp_server(
                    name=
                        self.MCP_SERVER_NAME,
                    version="1.0.0",
                    tools=sdk_tools,
                )
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
                for definition
                in tools
            ]

        options = ClaudeAgentOptions(
            model=self.model,
            system_prompt=system,

            # Claude Code built-in
            # tools are disabled.
            tools=[],

            mcp_servers=
                mcp_servers,

            allowed_tools=
                allowed_tools,

            permission_mode=
                "dontAsk",

            setting_sources=[],

            skills=[],

            max_turns=max_steps,

            include_partial_messages=
                partial_messages,

            env={
                "ANTHROPIC_API_KEY":
                    self.api_key,
            },
        )

        text_parts: list[
            str
        ] = []

        saw_partial_text = False

        final_result: (
            ResultMessage
            | None
        ) = None

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
                        StreamEvent,
                    ):
                        if (
                            not
                            partial_messages
                        ):
                            continue

                        event = (
                            message.event
                            or {}
                        )

                        if (
                            event.get(
                                "type"
                            )
                            !=
                            "content_block_delta"
                        ):
                            continue

                        delta = (
                            event.get(
                                "delta"
                            )
                            or {}
                        )

                        # IMPORTANT:
                        # Only user-visible text
                        # is streamed.
                        #
                        # thinking_delta /
                        # reasoning data is
                        # intentionally ignored.
                        if (
                            delta.get(
                                "type"
                            )
                            != "text_delta"
                        ):
                            continue

                        text = (
                            delta.get(
                                "text"
                            )
                            or ""
                        )

                        if (
                            not isinstance(
                                text,
                                str,
                            )
                            or not text
                        ):
                            continue

                        saw_partial_text = (
                            True
                        )

                        text_parts.append(
                            text
                        )

                        if (
                            event_sink
                            is not None
                        ):
                            event_sink(
                                ClaudeAgentSDKStreamItem(
                                    type=
                                        "delta",
                                    delta=
                                        text,
                                )
                            )

                    elif isinstance(
                        message,
                        AssistantMessage,
                    ):
                        # Non-streaming run()
                        # path keeps the old
                        # complete-message
                        # behaviour.
                        if (
                            not
                            partial_messages
                        ):
                            for block in (
                                message.content
                            ):
                                if isinstance(
                                    block,
                                    TextBlock,
                                ):
                                    if (
                                        block.text
                                    ):
                                        text_parts.append(
                                            block.text
                                        )

                        # Defensive fallback:
                        # If this SDK runtime
                        # advertises partial
                        # messages but emits no
                        # text_delta at all,
                        # preserve a usable
                        # response.
                        elif (
                            not
                            saw_partial_text
                        ):
                            fallback_parts = [
                                block.text
                                for block
                                in message.content
                                if (
                                    isinstance(
                                        block,
                                        TextBlock,
                                    )
                                    and
                                    block.text
                                )
                            ]

                            if (
                                fallback_parts
                            ):
                                fallback_text = (
                                    "".join(
                                        fallback_parts
                                    )
                                )

                                text_parts.append(
                                    fallback_text
                                )

                                if (
                                    event_sink
                                    is not None
                                ):
                                    event_sink(
                                        ClaudeAgentSDKStreamItem(
                                            type=
                                                "delta",
                                            delta=
                                                fallback_text,
                                        )
                                    )

                    elif isinstance(
                        message,
                        ResultMessage,
                    ):
                        final_result = (
                            message
                        )

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

        if (
            partial_messages
            and text_parts
        ):
            final_text = "".join(
                text_parts
            )
        else:
            final_text = (
                final_result.result
                or "".join(
                    text_parts
                )
            )

        usage = (
            final_result.usage
            or {}
        )

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
            tool_calls=
                tool_calls,
            metadata={
                "agent_sdk":
                    True,
                "session_id":
                    final_result
                    .session_id,
                "num_turns":
                    final_result
                    .num_turns,
                "total_cost_usd":
                    final_result
                    .total_cost_usd,
                "stop_reason":
                    final_result
                    .stop_reason,
            },
        )

    def run(
        self,
        messages: list[
            LLMMessage
        ],
        *,
        tools: list[
            LLMToolDefinition
        ],
        tool_executor:
            ToolExecutor,
        system:
            str | None = None,
        max_steps:
            int = 4,
    ) -> ClaudeAgentSDKResult:
        if not messages:
            raise ValueError(
                "Mesaj listesi bos olamaz."
            )

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return _run_sdk_coroutine(
                self._run_async(
                    messages,
                    tools=tools,
                    tool_executor=
                        tool_executor,
                    system=system,
                    max_steps=
                        max_steps,
                    partial_messages=
                        False,
                )
            )

        raise RuntimeError(
            "ClaudeAgentSDKAdapter.run() "
            "aktif async event loop icinden "
            "cagrilamaz."
        )

    def stream(
        self,
        messages: list[
            LLMMessage
        ],
        *,
        tools: list[
            LLMToolDefinition
        ],
        tool_executor:
            ToolExecutor,
        system:
            str | None = None,
        max_steps:
            int = 4,
    ):
        """
        Async Claude Agent SDK stream'ini
        mevcut sync VERITAS provider
        contract'ina bridge eder.

        SDK event loop ayri worker thread
        icinde calisir. Gelen eventler
        thread-safe queue ile Django SSE
        generator'ina aktarilir.
        """

        if not messages:
            raise ValueError(
                "Mesaj listesi bos olamaz."
            )

        event_queue: queue.Queue[
            object
        ] = queue.Queue()

        sentinel = object()

        def emit(
            item:
                ClaudeAgentSDKStreamItem,
        ) -> None:
            event_queue.put(
                item
            )

        def worker() -> None:
            try:
                result = _run_sdk_coroutine(
                    self._run_async(
                        messages,
                        tools=tools,
                        tool_executor=
                            tool_executor,
                        system=system,
                        max_steps=
                            max_steps,
                        partial_messages=
                            True,
                        event_sink=
                            emit,
                    )
                )

                event_queue.put(
                    ClaudeAgentSDKStreamItem(
                        type="done",
                        result=result,
                    )
                )

            except Exception as exc:
                event_queue.put(
                    exc
                )

            finally:
                event_queue.put(
                    sentinel
                )

        thread = threading.Thread(
            target=worker,
            name=(
                "veritas-claude-"
                "stream"
            ),
            daemon=True,
        )

        thread.start()

        while True:
            item = (
                event_queue.get()
            )

            if item is sentinel:
                break

            if isinstance(
                item,
                Exception,
            ):
                raise item

            if isinstance(
                item,
                ClaudeAgentSDKStreamItem,
            ):
                yield item
