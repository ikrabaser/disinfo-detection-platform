from __future__ import annotations

import pytest

from accounts.models import (
    Role,
    User,
)
from agent.models import (
    Conversation,
    Message,
)
from agent.services import (
    AssistantService,
)
from llm import (
    LLMResponse,
    LLMStreamEvent,
)


class FakeStreamingProvider:
    name = "fake-stream"
    model = "fake-stream-model"
    configured = True
    supports_tools = True

    def generate_with_tools(
        self,
        messages,
        *,
        tools,
        tool_executor,
        system=None,
        max_steps=4,
    ):
        return LLMResponse(
            text="Merhaba dunya",
            provider=self.name,
            model=self.model,
            input_tokens=10,
            output_tokens=4,
            tool_calls=[],
        )

    def stream_with_tools(
        self,
        messages,
        *,
        tools,
        tool_executor,
        system=None,
        max_steps=4,
    ):
        yield LLMStreamEvent(
            type="delta",
            delta="Merhaba ",
        )

        yield LLMStreamEvent(
            type="tool_start",
            tool_call={
                "id": "tool-1",
                "name":
                    "get_analysis_result",
            },
        )

        yield LLMStreamEvent(
            type="tool_end",
            tool_call={
                "id": "tool-1",
                "name":
                    "get_analysis_result",
                "status":
                    "success",
            },
        )

        yield LLMStreamEvent(
            type="delta",
            delta="dunya",
        )

        yield LLMStreamEvent(
            type="done",
            response=LLMResponse(
                text="Merhaba dunya",
                provider=self.name,
                model=self.model,
                input_tokens=10,
                output_tokens=4,
                tool_calls=[
                    {
                        "id": "tool-1",
                        "name":
                            "get_analysis_result",
                        "status":
                            "success",
                    }
                ],
            ),
        )


@pytest.mark.django_db
def test_assistant_stream_persists_final_message():
    user = User.objects.create_user(
        username="stream-user",
        password="pass12345",
        role=Role.ANALYST,
    )

    conversation = (
        Conversation.objects.create(
            user=user,
            provider="fake-stream",
            model="fake-stream-model",
        )
    )

    service = AssistantService(
        user=user,
        conversation=conversation,
        provider=
            FakeStreamingProvider(),
    )

    events = list(
        service.stream_send(
            "Streaming testi"
        )
    )

    assert [
        item["event"]
        for item in events
    ] == [
        "start",
        "delta",
        "tool_start",
        "tool_end",
        "delta",
        "done",
    ]

    assert (
        Message.objects.filter(
            conversation=conversation
        ).count()
        == 2
    )

    assistant = (
        Message.objects
        .filter(
            conversation=conversation,
            role="assistant",
        )
        .get()
    )

    assert (
        assistant.content
        == "Merhaba dunya"
    )

    assert (
        assistant.metadata[
            "streamed"
        ]
        is True
    )


@pytest.mark.django_db
def test_regenerate_replaces_last_assistant_without_duplicate_user():
    user = User.objects.create_user(
        username="regenerate-user",
        password="pass12345",
        role=Role.ANALYST,
    )

    conversation = (
        Conversation.objects.create(
            user=user,
            provider="fake-stream",
            model="fake-stream-model",
        )
    )

    user_message = (
        Message.objects.create(
            conversation=conversation,
            role="user",
            content="Ayni soruyu koru",
        )
    )

    old_assistant = (
        Message.objects.create(
            conversation=conversation,
            role="assistant",
            content="Eski cevap",
            provider="fake-stream",
            model="old-model",
        )
    )

    service = AssistantService(
        user=user,
        conversation=conversation,
        provider=
            FakeStreamingProvider(),
    )

    (
        replaced_id,
        new_assistant,
    ) = service.regenerate_last()

    assert (
        replaced_id
        == old_assistant.id
    )

    assert (
        Message.objects.filter(
            conversation=conversation,
            role="user",
        ).count()
        == 1
    )

    assert (
        Message.objects.filter(
            conversation=conversation,
            role="assistant",
        ).count()
        == 1
    )

    assert (
        Message.objects.filter(
            pk=user_message.id
        ).exists()
        is True
    )

    assert (
        Message.objects.filter(
            pk=old_assistant.id
        ).exists()
        is False
    )

    assert (
        new_assistant.content
        == "Merhaba dunya"
    )

    assert (
        new_assistant.metadata[
            "regenerated"
        ]
        is True
    )


@pytest.mark.django_db
def test_edit_user_message_replaces_following_branch():
    user = User.objects.create_user(
        username="edit-branch-user",
        password="pass12345",
        role=Role.ANALYST,
    )

    conversation = (
        Conversation.objects.create(
            user=user,
            provider="fake-stream",
            model="fake-stream-model",
        )
    )

    first_user = (
        Message.objects.create(
            conversation=conversation,
            role="user",
            content="Eski ilk soru",
        )
    )

    first_assistant = (
        Message.objects.create(
            conversation=conversation,
            role="assistant",
            content="Eski ilk cevap",
            provider="fake-stream",
            model="old-model",
        )
    )

    second_user = (
        Message.objects.create(
            conversation=conversation,
            role="user",
            content="Ikinci soru",
        )
    )

    second_assistant = (
        Message.objects.create(
            conversation=conversation,
            role="assistant",
            content="Ikinci cevap",
            provider="fake-stream",
            model="old-model",
        )
    )

    service = AssistantService(
        user=user,
        conversation=conversation,
        provider=
            FakeStreamingProvider(),
    )

    (
        edited_message,
        new_assistant,
        deleted_ids,
    ) = (
        service
        .edit_user_message_and_regenerate(
            message_id=
                first_user.id,
            content=
                "Duzenlenmis ilk soru",
        )
    )

    edited_message.refresh_from_db()

    assert (
        edited_message.content
        == "Duzenlenmis ilk soru"
    )

    assert set(
        deleted_ids
    ) == {
        first_assistant.id,
        second_user.id,
        second_assistant.id,
    }

    assert (
        Message.objects.filter(
            conversation=conversation,
            role="user",
        ).count()
        == 1
    )

    assert (
        Message.objects.filter(
            conversation=conversation,
            role="assistant",
        ).count()
        == 1
    )

    assert (
        new_assistant.content
        == "Merhaba dunya"
    )

    assert (
        new_assistant.metadata[
            "edited_branch"
        ]
        is True
    )


@pytest.mark.django_db
def test_edit_rejects_assistant_message():
    user = User.objects.create_user(
        username="edit-assistant-user",
        password="pass12345",
        role=Role.ANALYST,
    )

    conversation = (
        Conversation.objects.create(
            user=user,
            provider="fake-stream",
            model="fake-stream-model",
        )
    )

    assistant = (
        Message.objects.create(
            conversation=conversation,
            role="assistant",
            content="Assistant response",
            provider="fake-stream",
            model="fake-stream-model",
        )
    )

    service = AssistantService(
        user=user,
        conversation=conversation,
        provider=
            FakeStreamingProvider(),
    )

    with pytest.raises(
        ValueError,
        match="Yalnizca kullanici",
    ):
        (
            service
            .edit_user_message_and_regenerate(
                message_id=
                    assistant.id,
                content="Degistir",
            )
        )
