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


@pytest.mark.django_db
def test_owner_can_rename_conversation():
    user = User.objects.create_user(
        username="rename-owner",
        password="pass12345",
        role=Role.ANALYST,
    )

    conversation = (
        Conversation.objects.create(
            user=user,
            provider="openai",
            model="test-model",
            title="Eski baslik",
        )
    )

    client = APIClient()

    client.force_authenticate(
        user=user
    )

    response = client.patch(
        (
            "/api/agent/"
            f"conversations/{conversation.id}/"
        ),
        {
            "title":
                "Yeni sohbet basligi"
        },
        format="json",
    )

    assert response.status_code == 200

    conversation.refresh_from_db()

    assert (
        conversation.title
        == "Yeni sohbet basligi"
    )


@pytest.mark.django_db
def test_user_cannot_rename_foreign_conversation():
    owner = User.objects.create_user(
        username="rename-real-owner",
        password="pass12345",
        role=Role.ANALYST,
    )

    other = User.objects.create_user(
        username="rename-other",
        password="pass12345",
        role=Role.ANALYST,
    )

    conversation = (
        Conversation.objects.create(
            user=owner,
            provider="openai",
            model="test-model",
        )
    )

    client = APIClient()

    client.force_authenticate(
        user=other
    )

    response = client.patch(
        (
            "/api/agent/"
            f"conversations/{conversation.id}/"
        ),
        {
            "title":
                "Yetkisiz degisiklik"
        },
        format="json",
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_blank_conversation_title_is_rejected():
    user = User.objects.create_user(
        username="rename-blank",
        password="pass12345",
        role=Role.ANALYST,
    )

    conversation = (
        Conversation.objects.create(
            user=user,
            provider="openai",
            model="test-model",
        )
    )

    client = APIClient()

    client.force_authenticate(
        user=user
    )

    response = client.patch(
        (
            "/api/agent/"
            f"conversations/{conversation.id}/"
        ),
        {
            "title": "   "
        },
        format="json",
    )

    assert response.status_code == 400


@pytest.mark.django_db
def test_user_cannot_bind_foreign_analysis_to_conversation():
    from analyses.models import Analysis

    owner = User.objects.create_user(
        username="analysis-chat-owner",
        password="pass12345",
        role=Role.ANALYST,
    )

    other = User.objects.create_user(
        username="analysis-chat-other",
        password="pass12345",
        role=Role.ANALYST,
    )

    analysis = Analysis.objects.create(
        claim_text="Private analysis",
        created_by=owner,
    )

    client = APIClient()

    client.force_authenticate(
        user=other
    )

    response = client.post(
        "/api/agent/conversations/",
        {
            "provider": "openai",
            "analysis_id":
                analysis.id,
        },
        format="json",
    )

    assert response.status_code == 404

    assert (
        Conversation.objects
        .filter(
            user=other,
            analysis=analysis,
        )
        .exists()
        is False
    )


@pytest.mark.django_db
def test_admin_can_bind_foreign_analysis_to_conversation():
    from analyses.models import Analysis

    owner = User.objects.create_user(
        username="analysis-admin-owner",
        password="pass12345",
        role=Role.ANALYST,
    )

    admin = User.objects.create_user(
        username="analysis-chat-admin",
        password="pass12345",
        role=Role.ADMIN,
    )

    analysis = Analysis.objects.create(
        claim_text="Admin accessible",
        created_by=owner,
    )

    client = APIClient()

    client.force_authenticate(
        user=admin
    )

    response = client.post(
        "/api/agent/conversations/",
        {
            "provider": "openai",
            "analysis_id":
                analysis.id,
        },
        format="json",
    )

    assert response.status_code == 201

    assert (
        response.data["analysis"]
        == analysis.id
    )
