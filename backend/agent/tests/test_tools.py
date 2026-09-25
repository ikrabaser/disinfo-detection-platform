import pytest

from accounts.models import Role, User
from bot_engine import inference as bot_inference
from graph_engine.models import PropagationGraph
from agent.client import AgentRunner
from agent.tools import get_news, get_social_posts, run_bot_analysis
from agent.tools.permissions import can_invoke_tool


def test_get_news_returns_mock_articles():
    articles = get_news(query="deprem", limit=2)
    assert len(articles) == 2
    assert all("title" in article for article in articles)


def test_get_social_posts_returns_mock_posts():
    posts = get_social_posts(query="sel", max_results=4)
    assert len(posts) == 4


@pytest.mark.django_db
def test_run_bot_analysis_uses_graph_profiles(
    monkeypatch,
):
    graph = PropagationGraph.objects.create(
        source_analysis_query="test",
        node_count=1,
        edge_count=0,
        nodes=[
            {
                "id": "post-1",
                "type": "post",
                "attrs": {
                    "author_id": "user-a",
                },
            }
        ],
        edges=[],
    )

    def fake_predict_graph_users(
        nodes,
    ):
        assert nodes == graph.nodes

        return {
            "user_count": 1,
            "scores": {
                "user-a": 0.8,
            },
            "predictions": {
                "user-a": {
                    "predicted_label":
                        "bot",
                    "bot_score":
                        0.8,
                    "human_score":
                        0.2,
                    "confidence":
                        0.8,
                }
            },
            "flagged_users": [
                "user-a",
            ],
            "flagged_count": 1,
            "average_bot_score":
                0.8,
            "max_bot_score":
                0.8,
            "model":
                "test-model",
            "model_type":
                "random_forest",
            "feature_set":
                "profile-13d",
            "training_dataset":
                "test-dataset",
            "training_samples":
                100,
            "cross_domain":
                True,
            "score_calibrated":
                False,
        }

    monkeypatch.setattr(
        bot_inference,
        "predict_graph_users",
        fake_predict_graph_users,
    )

    result = run_bot_analysis(
        graph_id=str(graph.pk)
    )

    assert result["graph_id"] == str(
        graph.pk
    )

    assert result[
        "scores"
    ]["user-a"] == 0.8

    assert result[
        "flagged_users"
    ] == [
        "user-a"
    ]


@pytest.mark.django_db
def test_can_invoke_tool_respects_role_restrictions():
    viewer = User.objects.create_user(username="viewer1", password="pass12345", role=Role.VIEWER)
    analyst = User.objects.create_user(username="analyst1", password="pass12345", role=Role.ANALYST)

    # run_bot_analysis sadece admin/analyst rolüne acik.
    assert can_invoke_tool(viewer, run_bot_analysis) is False
    assert can_invoke_tool(analyst, run_bot_analysis) is True


@pytest.mark.django_db
def test_agent_runner_returns_mock_when_no_api_key(settings):
    settings.DEFAULT_LLM_PROVIDER = "openai"
    settings.OPENAI_API_KEY = ""
    user = User.objects.create_user(username="tester2", password="pass12345", role=Role.ANALYST)
    runner = AgentRunner(user=user)
    result = runner.run("test prompt")
    assert result.structured_output["mock"] is True


from llm.schemas import LLMResponse


class FakeConfiguredProvider:
    name = "fake"
    model = "fake-model"
    configured = True

    def generate(
        self,
        messages,
        *,
        system=None,
    ):
        assert (
            messages[0].content
            == "VERITAS testi"
        )

        assert system is not None

        return LLMResponse(
            text="Gercek provider yaniti",
            provider=self.name,
            model=self.model,
            input_tokens=15,
            output_tokens=8,
            metadata={
                "test": True,
            },
        )


def test_agent_runner_uses_configured_provider():
    runner = AgentRunner(
        provider=FakeConfiguredProvider()
    )

    result = runner.run(
        "VERITAS testi"
    )

    assert (
        result.output_text
        == "Gercek provider yaniti"
    )

    assert result.provider == "fake"
    assert result.model == "fake-model"

    assert (
        result.structured_output[
            "mock"
        ]
        is False
    )

    assert (
        result.structured_output[
            "usage"
        ][
            "input_tokens"
        ]
        == 15
    )


@pytest.mark.django_db
def test_agent_runner_mock_uses_selected_provider(
    settings,
):
    settings.ANTHROPIC_API_KEY = ""

    user = User.objects.create_user(
        username="claude-user",
        password="pass12345",
        role=Role.ANALYST,
    )

    runner = AgentRunner(
        user=user,
        provider_name="claude",
    )

    result = runner.run(
        "Merhaba Claude"
    )

    assert (
        result.provider
        == "anthropic"
    )

    assert (
        result.structured_output[
            "mock"
        ]
        is True
    )
