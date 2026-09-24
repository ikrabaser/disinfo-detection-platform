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
