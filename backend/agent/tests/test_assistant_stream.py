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
