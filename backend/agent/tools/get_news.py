"""Agent tool: get_news."""
from agent.tools.permissions import tool_permission
from external.news_fetcher import fetch_news_articles


@tool_permission(roles={"admin", "analyst", "viewer"})
def get_news(query: str, limit: int = 5) -> list[dict]:
    """Verilen konuyla ilgili haber makalelerini getirir (mock).

    Args:
        query: Arama sorgusu (ör. "deprem yardim kampanyasi").
        limit: Donecek maksimum makale sayisi.

    Returns:
        Her biri {"id", "title", "url", "source", "published_at", "summary"}
        anahtarlarini iceren sozluklerden olusan liste.

    TODO: `external.news_fetcher.fetch_news_articles` gercek bir haber API'si
    ile degistirildiginde bu tool otomatik olarak gercek veri dondurecektir.
    """
    return fetch_news_articles(query=query, limit=limit)
