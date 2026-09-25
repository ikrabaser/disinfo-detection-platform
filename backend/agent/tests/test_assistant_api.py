import pytest
from rest_framework.test import (
    APIClient,
)

from accounts.models import (
    Role,
    User,
)
from agent.models import Conversation


@pytest.mark.django_db
def test_user_cannot_read_other_users_conversation():
    owner = User.objects.create_user(
        username="chat-owner",
        password="pass12345",
        role=Role.ANALYST,
    )

    other = User.objects.create_user(
        username="chat-other",
        password="pass12345",
        role=Role.ANALYST,
    )

    conversation = (
        Conversation.objects.create(
            user=owner,
            provider="openai",
            model="gpt-4o-mini",
        )
    )

    client = APIClient()
    client.force_authenticate(
        user=other
    )

    response = client.get(
        (
            "/api/agent/"
            f"conversations/{conversation.id}/"
        )
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_conversation_list_only_returns_current_user():
    user = User.objects.create_user(
        username="list-user",
        password="pass12345",
        role=Role.ANALYST,
    )

    other = User.objects.create_user(
        username="list-other",
        password="pass12345",
        role=Role.ANALYST,
    )

    Conversation.objects.create(
        user=user,
        provider="openai",
        model="gpt-4o-mini",
        title="Benim sohbetim",
    )

    Conversation.objects.create(
        user=other,
        provider="openai",
        model="gpt-4o-mini",
        title="Baska sohbet",
    )

    client = APIClient()
    client.force_authenticate(
        user=user
    )

    response = client.get(
        "/api/agent/conversations/"
    )

    assert response.status_code == 200

    conversations = (
        response.data[
            "conversations"
        ]
    )

    assert len(conversations) == 1

    assert (
        conversations[0]["title"]
        == "Benim sohbetim"
    )
