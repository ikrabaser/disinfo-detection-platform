from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from agent.tools import TOOL_REGISTRY
from agent.tools.permissions import can_invoke_tool
from llm import (
    LLMMessage,
    LLMProvider,
    get_llm_provider,
)


DEFAULT_SYSTEM_PROMPT = """
Sen VERITAS Analysis Platform icindeki AI asistansin.

Gorevin:
- analiz sonuclarini acik ve temkinli bicimde aciklamak,
- NLP, GNN ve bot tespit sinyallerini birbirinden ayirmak,
- model skorlarini kesin gerceklik olasiligi gibi sunmamak,
- cross-domain veya kalibre edilmemis sonuclarda bu sinirlari belirtmek,
- kullaniciya teknik ama anlasilir yanit vermek.

Bir model sinyali tek basina bir iddianin dogru veya yanlis oldugunu
kanitlamaz.
""".strip()


@dataclass
class AgentRunResult:
    output_text: str
    provider: str
    model: str

    tool_calls: list[dict] = field(
        default_factory=list
    )

    structured_output: dict | None = None


class AgentRunner:
    """
    VERITAS AI agent katmani.

    AgentRunner belirli bir LLM saglayicisina
    bagimli degildir. Gercek model cagrilari
    llm/ altindaki provider adapter'lari
    uzerinden yapilir.
    """

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
    ) -> dict:
        """
        Agent tool'unu RBAC kontrolunden
        sonra calistir.
        """

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
                "Kullanici "
                f"'{getattr(self.user, 'username', None)}' "
                f"'{tool_name}' tool'unu "
                "cagirma yetkisine sahip degil."
            )

        return tool_fn(**kwargs)

    def run(
        self,
        prompt: str,
    ) -> AgentRunResult:
        """
        Prompt'u secili LLM provider ile
        calistir.

        Provider configure edilmemisse local
        gelistirme icin deterministik mock
        response dondurulur.
        """

        normalized_prompt = prompt.strip()

        if not normalized_prompt:
            raise ValueError(
                "Prompt bos olamaz."
            )

        if not self.provider.configured:
            return AgentRunResult(
                output_text=(
                    "MOCK yanit: "
                    f"{self.provider.name} provider "
                    "configure edilmedigi icin "
                    "gercek LLM cagrisi yapilmadi. "
                    "Prompt: "
                    f"'{normalized_prompt[:120]}'"
                ),
                provider=self.provider.name,
                model=self.provider.model,
                tool_calls=[],
                structured_output={
                    "mock": True,
                    "provider":
                        self.provider.name,
                    "model":
                        self.provider.model,
                    "prompt_preview":
                        normalized_prompt[:120],
                },
            )

        response = self.provider.generate(
            [
                LLMMessage(
                    role="user",
                    content=normalized_prompt,
                )
            ],
            system=DEFAULT_SYSTEM_PROMPT,
        )

        return AgentRunResult(
            output_text=response.text,
            provider=response.provider,
            model=response.model,
            tool_calls=[],
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
                "metadata":
                    response.metadata,
            },
        )
