"""Agent tool: get_social_posts."""
from agent.tools.permissions import tool_permission
from external.x_client import get_x_api_client


@tool_permission(roles={"admin", "analyst", "viewer"})
def get_social_posts(query: str, max_results: int = 10) -> list[dict]:
    """Verilen konuyla ilgili sosyal medya (X/Twitter) paylasimlarini getirir (mock).

    Args:
        query: Arama sorgusu (ör. bir haber basligi veya hashtag).
        max_results: Donecek maksimum paylasim sayisi.

    Returns:
        Her biri {"id", "author_id", "text", "created_at", "shared_from_id",
        "like_count", "retweet_count"} anahtarlarini iceren liste.

    TODO: `external.x_client.get_x_api_client` gercek X API v2 istemcisi ile
    degistirildiginde bu tool gercek veri dondurecektir. Su an tamamen MOCK.
    """
    client = get_x_api_client()
    return client.search_recent_posts(query=query, max_results=max_results)
