from realtime.centrifugo_client import CentrifugoClient, get_centrifugo_client


def test_get_centrifugo_client_returns_client_instance():
    client = get_centrifugo_client()
    assert isinstance(client, CentrifugoClient)


def test_publish_analysis_progress_returns_mock_status():
    client = get_centrifugo_client()
    result = client.publish_analysis_progress(analysis_id=1, stage="nlp", progress=0.5)
    assert result["status"] == "mock-published"
    assert result["channel"] == "analysis:1"
