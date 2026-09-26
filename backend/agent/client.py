from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)
from typing import Any

from django.conf import settings

from agent.prompts import VERITAS_SYSTEM_PROMPT
from agent.tool_schemas import (
    build_assistant_tool_definitions,
)
from agent.tools import TOOL_REGISTRY
from agent.tools.permissions import (
    can_invoke_tool,
)
from llm import (
    LLMMessage,
    LLMProvider,
    get_llm_provider,
)


DEFAULT_SYSTEM_PROMPT = VERITAS_SYSTEM_PROMPT


@dataclass
class AgentRunResult:
    output_text: str
    provider: str
    model: str

    input_tokens: int | None = None
    output_tokens: int | None = None

    tool_calls: list[dict] = field(
        default_factory=list
    )

    structured_output: dict | None = None


class AgentRunner:
    def __init__(
        self,
        user=None,
        provider_name: str | None = None,
        provider: LLMProvider | None = None,
    ):
        self.user = user

        self.provider = (
            provider
            if provider is not None
            else get_llm_provider(
                provider_name
            )
        )

    def call_tool(
        self,
        tool_name: str,
        **kwargs: Any,
    ) -> Any:
        tool_fn = TOOL_REGISTRY.get(
            tool_name
        )

        if tool_fn is None:
            raise ValueError(
                f"Bilinmeyen tool: {tool_name}"
            )

        if not can_invoke_tool(
            self.user,
            tool_fn,
        ):
            raise PermissionError(
                "Kullanici bu tool'u "
                "cagirma yetkisine sahip degil."
            )

        if (
            tool_name
            == "get_analysis_result"
        ):
            from analyses.models import (
                Analysis,
            )

            analysis_id = kwargs.get(
                "analysis_id"
            )

            try:
                analysis = (
                    Analysis.objects
                    .only(
                        "created_by_id"
                    )
                    .get(
                        pk=analysis_id
                    )
                )
            except Analysis.DoesNotExist:
                analysis = None

            if (
                analysis is not None
                and getattr(
                    self.user,
                    "role",
                    None,
                )
                != "admin"
                and analysis.created_by_id
                != getattr(
                    self.user,
                    "id",
                    None,
                )
            ):
                raise PermissionError(
                    "Bu analysis kaydina "
                    "erisim yetkiniz yok."
                )

        return tool_fn(
            **kwargs
        )

    def _execute_tool(
        self,
        name: str,
        arguments: dict[str, Any],
    ) -> Any:
        return self.call_tool(
            name,
            **arguments,
        )

    def run_messages(
        self,
        messages: list[LLMMessage],
        *,
        system: str | None = None,
    ) -> AgentRunResult:
        if not messages:
            raise ValueError(
                "Mesaj listesi bos olamaz."
            )

        if not self.provider.configured:
            preview = (
                messages[-1].content[:120]
            )

            return AgentRunResult(
                output_text=(
                    "MOCK yanit: "
                    f"{self.provider.name} provider "
                    "configure edilmedigi icin "
                    "gercek LLM cagrisi yapilmadi. "
                    f"Prompt: '{preview}'"
                ),
                provider=
                    self.provider.name,
                model=
                    self.provider.model,
                tool_calls=[],
                structured_output={
                    "mock": True,
                    "provider":
                        self.provider.name,
                    "model":
                        self.provider.model,
                    "prompt_preview":
                        preview,
                },
            )

        tools = (
            build_assistant_tool_definitions(
                self.user
            )
        )

        supports_tools = bool(
            getattr(
                self.provider,
                "supports_tools",
                False,
            )
        )

        if (
            supports_tools
            and tools
        ):
            response = (
                self.provider
                .generate_with_tools(
                    messages,
                    tools=tools,
                    tool_executor=
                        self._execute_tool,
                    system=system,
                    max_steps=int(
                        getattr(
                            settings,
                            "AGENT_MAX_TOOL_STEPS",
                            4,
                        )
                    ),
                )
            )

        else:
            response = (
                self.provider.generate(
                    messages,
                    system=system,
                )
            )

        return AgentRunResult(
            output_text=
                response.text,
            provider=
                response.provider,
            model=response.model,
            input_tokens=
                response.input_tokens,
            output_tokens=
                response.output_tokens,
            tool_calls=
                response.tool_calls,
            structured_output={
                "mock": False,
                "provider":
                    response.provider,
                "model":
                    response.model,
                "usage": {
                    "input_tokens":
                        response.input_tokens,
                    "output_tokens":
                        response.output_tokens,
                },
                "tool_call_count":
                    len(
                        response.tool_calls
                    ),
                "metadata":
                    response.metadata,
            },
        )

    def stream_messages(
        self,
        messages: list[LLMMessage],
        *,
        system: str | None = None,
    ):
        if not messages:
            raise ValueError(
                "Mesaj listesi bos olamaz."
            )

        if not self.provider.configured:
            raise ValueError(
                f"{self.provider.name} "
                "provider configure edilmemis."
            )

        tools = (
            build_assistant_tool_definitions(
                self.user
            )
        )

        yield from (
            self.provider
            .stream_with_tools(
                messages,
                tools=tools,
                tool_executor=
                    self._execute_tool,
                system=system,
                max_steps=int(
                    getattr(
                        settings,
                        "AGENT_MAX_TOOL_STEPS",
                        4,
                    )
                ),
            )
        )


    def run(
        self,
        prompt: str,
    ) -> AgentRunResult:
        normalized_prompt = (
            prompt.strip()
        )

        if not normalized_prompt:
            raise ValueError(
                "Prompt bos olamaz."
            )

        return self.run_messages(
            [
                LLMMessage(
                    role="user",
                    content=
                        normalized_prompt,
                )
            ],
            system=
                DEFAULT_SYSTEM_PROMPT,
        )
