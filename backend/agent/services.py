from __future__ import annotations

import json

from django.conf import settings
from django.db import transaction

from agent.prompts import VERITAS_SYSTEM_PROMPT
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


ASSISTANT_SYSTEM_PROMPT = VERITAS_SYSTEM_PROMPT


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

    def edit_user_message_and_regenerate(
        self,
        *,
        message_id: int,
        content: str,
    ) -> tuple[
        Message,
        Message,
        list[int],
    ]:
        """
        Bir user mesajini duzenler ve o
        noktadan sonraki conversation
        branch'ini yeniden olusturur.

        Yeni LLM yaniti basarili olmadan
        mevcut DB mesaji veya sonraki
        branch degistirilmez.
        """

        normalized = (
            content.strip()
        )

        if not normalized:
            raise ValueError(
                "Mesaj bos olamaz."
            )

        messages = list(
            self.conversation
            .messages
            .order_by(
                "created_at",
                "id",
            )
        )

        target_index = None

        for index, message in enumerate(
            messages
        ):
            if message.id == message_id:
                target_index = index
                break

        if target_index is None:
            raise ValueError(
                "Duzenlenecek mesaj bulunamadi."
            )

        target = messages[
            target_index
        ]

        if (
            target.role
            != MessageRole.USER
        ):
            raise ValueError(
                "Yalnizca kullanici "
                "mesajlari duzenlenebilir."
            )

        if not self.provider.configured:
            raise LLMConfigurationError(
                f"{self.provider.name} "
                "provider configure edilmemis."
            )

        limit = int(
            getattr(
                settings,
                "ASSISTANT_HISTORY_MESSAGES",
                20,
            )
        )

        previous_messages = (
            messages[:target_index]
        )[-limit:]

        llm_messages = [
            LLMMessage(
                role=message.role,
                content=message.content,
            )
            for message
            in previous_messages
        ]

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

        deleted_message_ids = [
            message.id
            for message
            in messages[
                target_index + 1:
            ]
        ]

        with transaction.atomic():
            target.content = normalized

            target.save(
                update_fields=[
                    "content",
                ]
            )

            if deleted_message_ids:
                (
                    Message.objects
                    .filter(
                        conversation=
                            self.conversation,
                        id__in=
                            deleted_message_ids,
                    )
                    .delete()
                )

            assistant_message = (
                Message.objects.create(
                    conversation=
                        self.conversation,
                    role=(
                        MessageRole
                        .ASSISTANT
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
                        "edited_branch":
                            True,
                        "edited_user_message_id":
                            target.id,
                        "removed_message_count":
                            len(
                                deleted_message_ids
                            ),
                    },
                )
            )

            self.conversation.model = (
                response.model
            )

            self.conversation.save(
                update_fields=[
                    "model",
                    "updated_at",
                ]
            )

        return (
            target,
            assistant_message,
            deleted_message_ids,
        )


    def regenerate_last(
        self,
    ) -> tuple[
        int,
        Message,
    ]:
        """
        Son assistant cevabini, onceki
        user mesajini duplicate etmeden
        yeniden uretir.

        Yeni cevap basarili olmadan eski
        assistant mesaji silinmez.
        """

        messages = list(
            self.conversation
            .messages
            .order_by(
                "created_at",
                "id",
            )
        )

        if len(messages) < 2:
            raise ValueError(
                "Yeniden olusturulacak "
                "bir assistant cevabi yok."
            )

        previous_user = messages[-2]
        previous_assistant = messages[-1]

        if (
            previous_user.role
            != MessageRole.USER
            or previous_assistant.role
            != MessageRole.ASSISTANT
        ):
            raise ValueError(
                "Son sohbet turn'u "
                "yeniden olusturmaya uygun degil."
            )

        if not self.provider.configured:
            raise LLMConfigurationError(
                f"{self.provider.name} "
                "provider configure edilmemis."
            )

        limit = int(
            getattr(
                settings,
                "ASSISTANT_HISTORY_MESSAGES",
                20,
            )
        )

        history_messages = (
            messages[:-1]
        )[-limit:]

        llm_messages = [
            LLMMessage(
                role=message.role,
                content=message.content,
            )
            for message
            in history_messages
        ]

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

        replaced_message_id = (
            previous_assistant.id
        )

        with transaction.atomic():
            previous_assistant.delete()

            assistant_message = (
                Message.objects.create(
                    conversation=
                        self.conversation,
                    role=(
                        MessageRole
                        .ASSISTANT
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
                        "regenerated":
                            True,
                        "replaced_message_id":
                            replaced_message_id,
                    },
                )
            )

            self.conversation.model = (
                response.model
            )

            self.conversation.save(
                update_fields=[
                    "model",
                    "updated_at",
                ]
            )

        return (
            replaced_message_id,
            assistant_message,
        )


    def stream_send(
        self,
        content: str,
    ):
        normalized = (
            content.strip()
        )

        if not normalized:
            raise ValueError(
                "Mesaj bos olamaz."
            )

        if not self.provider.configured:
            raise LLMConfigurationError(
                f"{self.provider.name} "
                "provider configure edilmemis."
            )

        # History, yeni user message DB'ye
        # eklenmeden once alinmali. Aksi halde
        # modele ayni mesaj iki kez gider.
        llm_messages = (
            self._history()
        )

        llm_messages.append(
            LLMMessage(
                role="user",
                content=normalized,
            )
        )

        user_message = (
            Message.objects.create(
                conversation=
                    self.conversation,
                role=MessageRole.USER,
                content=normalized,
            )
        )

        yield {
            "event": "start",
            "user_message":
                user_message,
        }

        runner = AgentRunner(
            user=self.user,
            provider=self.provider,
        )

        final_response = None

        for event in (
            runner.stream_messages(
                llm_messages,
                system=(
                    self._system_prompt()
                ),
            )
        ):
            if event.type == "delta":
                yield {
                    "event": "delta",
                    "delta":
                        event.delta,
                }

            elif (
                event.type
                == "tool_start"
            ):
                yield {
                    "event":
                        "tool_start",
                    "tool_call":
                        event.tool_call
                        or {},
                }

            elif (
                event.type
                == "tool_end"
            ):
                yield {
                    "event":
                        "tool_end",
                    "tool_call":
                        event.tool_call
                        or {},
                }

            elif event.type == "done":
                final_response = (
                    event.response
                )

        if (
            final_response is None
            or not
            final_response.text.strip()
        ):
            raise LLMProviderError(
                "LLM bos yanit dondurdu."
            )

        with transaction.atomic():
            assistant_message = (
                Message.objects.create(
                    conversation=
                        self.conversation,
                    role=(
                        MessageRole
                        .ASSISTANT
                    ),
                    content=
                        final_response.text,
                    provider=
                        final_response
                        .provider,
                    model=
                        final_response
                        .model,
                    input_tokens=
                        final_response
                        .input_tokens,
                    output_tokens=
                        final_response
                        .output_tokens,
                    metadata={
                        "tool_calls":
                            final_response
                            .tool_calls,
                        "streamed":
                            True,
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
                final_response.model
            )

            self.conversation.save(
                update_fields=[
                    "title",
                    "model",
                    "updated_at",
                ]
            )

        yield {
            "event": "done",
            "user_message":
                user_message,
            "assistant_message":
                assistant_message,
        }
