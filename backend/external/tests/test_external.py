from external.news_fetcher import fetch_news_articles
from external.x_client import get_x_api_client


def test_get_x_api_client_returns_mock_client():
    client = get_x_api_client()
    posts = client.search_recent_posts("deprem", max_results=3)
    assert len(posts) == 3
    assert all("text" in post for post in posts)


def test_fetch_news_articles_returns_mock_list():
    articles = fetch_news_articles("sel felaketi", limit=2)
    assert len(articles) == 2
    assert all("title" in article for article in articles)
