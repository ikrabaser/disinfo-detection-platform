from __future__ import annotations

import json

from django.conf import settings
from django.db import transaction

from agent.client import AgentRunner
from agent.models import (
    Conversation,
    Message,
    MessageRole,
)
from llm import (
    LLMConfigurationError,
    LLMMessage,
    LLMProviderError,
    get_llm_provider,
)


ASSISTANT_SYSTEM_PROMPT = """
Sen VERITAS Analysis Platform icindeki AI asistansin.

Gorevin:
- analiz sonuclarini teknik ama anlasilir bicimde aciklamak,
- NLP, GNN, bot ve evidence/RAG sonuclarini birbirinden ayirmak,
- model skorlarini kesin gerceklik olasiligi gibi sunmamak,
- cross-domain veya kalibre edilmemis sinyallerin sinirlarini belirtmek,
- yalnizca verilen analiz context'inde bulunmayan bilgileri uydurmamak,
- evidence yetersizse bunu acikca belirtmek,
- politik veya secimle ilgili konularda tarafsiz ve bilgilendirici kalmak,
- aday, parti veya oy tercihi konusunda tavsiye vermemek,
- siyasi aktorleri siralamamak veya secim sonucu tahmini yapmamak.

Bir ML modeli veya LLM sinyali tek basina bir iddianin dogru ya da
yanlis oldugunu kanitlamaz.
""".strip()


def build_analysis_context(
    conversation: Conversation,
) -> str | None:
    analysis = conversation.analysis

    if analysis is None:
        return None

    payload = {
        "analysis_id":
            analysis.id,
        "claim_text":
            analysis.claim_text,
        "source_url":
            analysis.source_url,
        "status":
            analysis.status,
        "nlp_result":
            analysis.nlp_result,
        "gnn_result":
            analysis.gnn_result,
        "bot_analysis_result":
            analysis.bot_analysis_result,
        "ai_analysis_result":
            analysis.ai_analysis_result,
        "truth_score":
            analysis.truth_score,
    }

    return (
        "Bu sohbet asagidaki VERITAS "
        "analizine baglidir.\n\n"
        + json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )
    )


class AssistantService:
    def __init__(
        self,
        *,
        user,
        conversation: Conversation,
        provider=None,
    ):
        if (
            conversation.user_id
            != user.id
        ):
            raise PermissionError(
                "Bu sohbete erisim yetkiniz yok."
            )

        self.user = user
        self.conversation = (
            conversation
        )

        self.provider = (
            provider
            if provider is not None
            else get_llm_provider(
                conversation.provider
            )
        )

    def _system_prompt(self) -> str:
        context = build_analysis_context(
            self.conversation
        )

        if not context:
            return (
                ASSISTANT_SYSTEM_PROMPT
            )

        return (
            f"{ASSISTANT_SYSTEM_PROMPT}"
            "\n\n"
            "ANALIZ CONTEXT:\n"
            f"{context}"
        )

    def _history(
        self,
    ) -> list[LLMMessage]:
        limit = int(
            getattr(
                settings,
                "ASSISTANT_HISTORY_MESSAGES",
                20,
            )
        )

        messages = list(
            self.conversation
            .messages
            .order_by(
                "-created_at",
                "-id",
            )[:limit]
        )

        messages.reverse()

        return [
            LLMMessage(
                role=message.role,
                content=message.content,
            )
            for message in messages
        ]

    @transaction.atomic
    def send(
        self,
        content: str,
    ) -> tuple[
        Message,
        Message,
    ]:
        normalized = (
            content.strip()
        )

        if not normalized:
            raise ValueError(
                "Mesaj bos olamaz."
            )

        if not self.provider.configured:
            raise (
                LLMConfigurationError(
                    f"{self.provider.name} "
                    "provider configure "
                    "edilmemis."
                )
            )

        llm_messages = (
            self._history()
        )

        llm_messages.append(
            LLMMessage(
                role="user",
                content=normalized,
            )
        )

        runner = AgentRunner(
            user=self.user,
            provider=self.provider,
        )

        response = (
            runner.run_messages(
                llm_messages,
                system=(
                    self._system_prompt()
                ),
            )
        )

        if not response.output_text.strip():
            raise LLMProviderError(
                "LLM bos yanit dondurdu."
            )

        user_message = (
            Message.objects.create(
                conversation=
                    self.conversation,
                role=MessageRole.USER,
                content=normalized,
            )
        )

        assistant_message = (
            Message.objects.create(
                conversation=
                    self.conversation,
                role=(
                    MessageRole.ASSISTANT
                ),
                content=
                    response.output_text,
                provider=
                    response.provider,
                model=response.model,
                input_tokens=
                    response.input_tokens,
                output_tokens=
                    response.output_tokens,
                metadata={
                    "tool_calls":
                        response.tool_calls,
                    "agent":
                        response.structured_output
                        or {},
                },
            )
        )

        if (
            self.conversation.title
            == "Yeni sohbet"
        ):
            self.conversation.title = (
                normalized[:80]
            )

        self.conversation.model = (
            response.model
        )

        self.conversation.save(
            update_fields=[
                "title",
                "model",
                "updated_at",
            ]
        )

        return (
            user_message,
            assistant_message,
        )
