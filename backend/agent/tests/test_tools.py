import pytest

from accounts.models import Role, User
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


def test_run_bot_analysis_flags_high_score_users():
    result = run_bot_analysis(user_ids=["user-a", "user-b"])
    assert set(result["scores"].keys()) == {"user-a", "user-b"}
    assert all(0.0 <= score <= 1.0 for score in result["scores"].values())


@pytest.mark.django_db
def test_can_invoke_tool_respects_role_restrictions():
    viewer = User.objects.create_user(username="viewer1", password="pass12345", role=Role.VIEWER)
    analyst = User.objects.create_user(username="analyst1", password="pass12345", role=Role.ANALYST)

    # run_bot_analysis sadece admin/analyst rolüne acik.
    assert can_invoke_tool(viewer, run_bot_analysis) is False
    assert can_invoke_tool(analyst, run_bot_analysis) is True


@pytest.mark.django_db
def test_agent_runner_returns_mock_when_no_api_key(settings):
    settings.OPENAI_API_KEY = ""
    user = User.objects.create_user(username="tester2", password="pass12345", role=Role.ANALYST)
    runner = AgentRunner(user=user)
    result = runner.run("test prompt")
    assert result.structured_output["mock"] is True
