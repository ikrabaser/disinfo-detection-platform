from unittest.mock import Mock, patch

from realtime.centrifugo_client import (
    CentrifugoClient,
    get_centrifugo_client,
)


def test_get_centrifugo_client_returns_client_instance():
    client = get_centrifugo_client()

    assert isinstance(
        client,
        CentrifugoClient,
    )


@patch(
    "realtime.centrifugo_client.httpx.post"
)
def test_publish_analysis_progress_success(
    mock_post,
):
    response = Mock()

    response.raise_for_status.return_value = None
    response.json.return_value = {
        "result": {}
    }

    mock_post.return_value = response

    client = get_centrifugo_client()

    result = (
        client.publish_analysis_progress(
            analysis_id=1,
            stage="gnn",
            progress=0.6,
        )
    )

    assert (
        result["status"]
        == "published"
    )

    assert (
        result["channel"]
        == "analysis:1"
    )

    mock_post.assert_called_once()


@patch(
    "realtime.centrifugo_client.httpx.post"
)
def test_publish_handles_centrifugo_api_error(
    mock_post,
):
    response = Mock()

    response.raise_for_status.return_value = None
    response.json.return_value = {
        "error": {
            "code": 102,
            "message": "unknown channel",
        }
    }

    mock_post.return_value = response

    client = get_centrifugo_client()

    result = client.publish(
        channel="invalid:test",
        data={
            "stage": "test",
        },
    )

    assert (
        result["status"]
        == "publish-failed"
    )


import jwt
import pytest
from django.conf import settings
from rest_framework.test import APIClient

from accounts.models import (
    Role,
    User,
)
from analyses.models import Analysis


@pytest.mark.django_db
def test_connection_token_contains_user():
    user = User.objects.create_user(
        username="realtime-user",
        password="testpass123",
        role=Role.VIEWER,
    )

    client = APIClient()
    client.force_authenticate(
        user=user
    )

    response = client.get(
        "/api/realtime/connect-token/"
    )

    assert response.status_code == 200

    payload = jwt.decode(
        response.data["token"],
        settings.CENTRIFUGO_HMAC_SECRET,
        algorithms=["HS256"],
    )

    assert payload["sub"] == str(
        user.pk
    )

    assert "exp" in payload


@pytest.mark.django_db
def test_subscription_token_is_channel_bound():
    user = User.objects.create_user(
        username="channel-user",
        password="testpass123",
        role=Role.VIEWER,
    )

    analysis = Analysis.objects.create(
        claim_text="Realtime test"
    )

    channel = (
        f"analysis:{analysis.pk}"
    )

    client = APIClient()
    client.force_authenticate(
        user=user
    )

    response = client.post(
        "/api/realtime/subscription-token/",
        {
            "channel": channel,
        },
        format="json",
    )

    assert response.status_code == 200

    payload = jwt.decode(
        response.data["token"],
        settings.CENTRIFUGO_HMAC_SECRET,
        algorithms=["HS256"],
    )

    assert payload["sub"] == str(
        user.pk
    )

    assert payload["channel"] == channel

    assert "exp" in payload


@pytest.mark.django_db
def test_subscription_token_rejects_invalid_channel():
    user = User.objects.create_user(
        username="bad-channel-user",
        password="testpass123",
        role=Role.VIEWER,
    )

    client = APIClient()
    client.force_authenticate(
        user=user
    )

    response = client.post(
        "/api/realtime/subscription-token/",
        {
            "channel": "admin:everything",
        },
        format="json",
    )

    assert response.status_code == 403
