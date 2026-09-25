from __future__ import annotations

from types import SimpleNamespace

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
from analyses.models import Analysis
from llm.schemas import LLMResponse


class FakeProvider:
    name = "fake"
    model = "fake-model"
    configured = True

    def __init__(self):
        self.last_messages = None
        self.last_system = None

    def generate(
        self,
        messages,
        *,
        system=None,
    ):
        self.last_messages = messages
        self.last_system = system

        return LLMResponse(
            text="Assistant cevabi",
            provider=self.name,
            model=self.model,
            input_tokens=12,
            output_tokens=7,
            metadata={
                "test": True,
            },
        )


@pytest.mark.django_db
def test_assistant_service_stores_messages():
    user = User.objects.create_user(
        username="assistant-user",
        password="pass12345",
        role=Role.ANALYST,
    )

    conversation = (
        Conversation.objects.create(
            user=user,
            provider="fake",
            model="fake-model",
        )
    )

    service = AssistantService(
        user=user,
        conversation=conversation,
        provider=FakeProvider(),
    )

    user_message, assistant_message = (
        service.send(
            "Bu analizi aciklar misin?"
        )
    )

    assert (
        user_message.role
        == "user"
    )

    assert (
        assistant_message.role
        == "assistant"
    )

    assert (
        assistant_message.content
        == "Assistant cevabi"
    )

    assert (
        assistant_message.input_tokens
        == 12
    )

    assert (
        Message.objects.filter(
            conversation=conversation
        ).count()
        == 2
    )

    conversation.refresh_from_db()

    assert (
        conversation.title
        == "Bu analizi aciklar misin?"
    )


@pytest.mark.django_db
def test_assistant_includes_analysis_context():
    user = User.objects.create_user(
        username="context-user",
        password="pass12345",
        role=Role.ANALYST,
    )

    analysis = Analysis.objects.create(
        claim_text=(
            "Ornek dezenformasyon iddiasi"
        ),
        created_by=user,
        nlp_result={
            "label": "sahte"
        },
        ai_analysis_result={
            "status": "completed",
            "report": {
                "overall_evidence_status":
                    "contradicted"
            },
        },
    )

    conversation = (
        Conversation.objects.create(
            user=user,
            analysis=analysis,
            provider="fake",
            model="fake-model",
        )
    )

    provider = FakeProvider()

    service = AssistantService(
        user=user,
        conversation=conversation,
        provider=provider,
    )

    service.send(
        "Neden contradicted?"
    )

    assert provider.last_system

    assert (
        "Ornek dezenformasyon iddiasi"
        in provider.last_system
    )

    assert (
        "contradicted"
        in provider.last_system
    )


@pytest.mark.django_db
def test_assistant_rejects_foreign_conversation():
    owner = User.objects.create_user(
        username="owner-user",
        password="pass12345",
        role=Role.ANALYST,
    )

    other = User.objects.create_user(
        username="other-user",
        password="pass12345",
        role=Role.ANALYST,
    )

    conversation = (
        Conversation.objects.create(
            user=owner,
            provider="fake",
            model="fake-model",
        )
    )

    with pytest.raises(
        PermissionError
    ):
        AssistantService(
            user=other,
            conversation=conversation,
            provider=FakeProvider(),
        )
