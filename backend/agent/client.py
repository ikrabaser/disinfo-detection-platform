"""
AgentRunner - OpenAI Agents SDK / OpenAI API sarmalayicisi.

Bu modul, `openai` python paketini kullanarak (API anahtari env'den okunur:
`OPENAI_API_KEY`) tool-calling (function calling) ve structured output
destegi olan bir ajan calistirir.

ONEMLI: Bu proje iskeletinde GERCEK bir OpenAI API cagrisi YAPILMAZ.
`OPENAI_API_KEY` bos oldugunda (varsayilan gelistirme durumu),
`AgentRunner.run()` MOCK bir yanit doner. Gercek entegrasyon icin asagidaki
TODO'lara bakin.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from django.conf import settings

from agent.tools import TOOL_REGISTRY
from agent.tools.permissions import can_invoke_tool

logger = logging.getLogger(__name__)


@dataclass
class AgentRunResult:
    output_text: str
    tool_calls: list[dict] = field(default_factory=list)
    structured_output: dict | None = None


class AgentRunner:
    """Dezenformasyon analizi icin tool-calling destekli AI ajani.

    TODO (gercek implementasyon):
        from openai import OpenAI
        self._client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # OpenAI Agents SDK kullanilacaksa:
        # from agents import Agent, Runner
        # self._agent = Agent(
        #     name="Dezenformasyon Analiz Ajani",
        #     model=settings.OPENAI_AGENT_MODEL,
        #     tools=[... function tool tanimlari ...],
        # )
    """

    def __init__(self, user=None):
        self.user = user
        self.model = settings.OPENAI_AGENT_MODEL
        self._client = None  # lazy-init

    def _get_client(self):
        """OpenAI istemcisini lazy-import ile olusturur."""
        if self._client is not None:
            return self._client
        try:
            from openai import OpenAI

            self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
            return self._client
        except ImportError as exc:
            raise ImportError(
                "openai paketi kurulu degil. `pip install openai` ile kurun."
            ) from exc

    def call_tool(self, tool_name: str, **kwargs: Any) -> dict:
        """Bir agent tool'unu, kullanicinin rol iznini kontrol ederek cagirir.

        RBAC: her tool `@tool_permission(roles=...)` ile etiketlenmistir
        (bkz. agent/tools/permissions.py). Yetkisiz bir kullanici bu tool'u
        cagirmaya calisirsa PermissionError firlatilir.
        """
        tool_fn = TOOL_REGISTRY.get(tool_name)
        if tool_fn is None:
            raise ValueError(f"Bilinmeyen tool: {tool_name}")

        if not can_invoke_tool(self.user, tool_fn):
            raise PermissionError(
                f"Kullanici '{getattr(self.user, 'username', None)}' "
                f"'{tool_name}' tool'unu cagirma yetkisine sahip degil."
            )

        return tool_fn(**kwargs)

    def run(self, prompt: str) -> AgentRunResult:
        """Kullanici promptunu isler ve (mock) bir agent yaniti doner.

        Gercek implementasyonda bu metod:
          1. OpenAI'a prompt + tool semalarini gonderir.
          2. Model bir tool cagirmak isterse, `self.call_tool(...)` ile
             calistirir ve sonucu modele geri gonderir (function calling loop).
          3. Nihai (structured) yaniti doner.

        Su an OPENAI_API_KEY bos oldugu icin gercek bir cagri yapilmiyor;
        bunun yerine deterministik bir MOCK yanit uretiliyor.
        """
        if not settings.OPENAI_API_KEY:
            logger.info("[AgentRunner] OPENAI_API_KEY bos - MOCK yanit donuluyor.")
            return AgentRunResult(
                output_text=(
                    "MOCK yanit: OPENAI_API_KEY tanimli olmadigi icin gercek bir "
                    f"LLM cagrisi yapilmadi. Alinan prompt: '{prompt[:120]}'"
                ),
                tool_calls=[],
                structured_output={"mock": True, "prompt_preview": prompt[:120]},
            )

        # TODO: gercek OpenAI Agents SDK / function-calling loop implementasyonu.
        client = self._get_client()  # noqa: F841 - gercek implementasyon icin kullanilacak
        raise NotImplementedError(
            "Gercek OpenAI entegrasyonu bu proje iskeletinin kapsami disindadir. "
            "OPENAI_API_KEY bos birakildiginda mock moda dusulur."
        )
