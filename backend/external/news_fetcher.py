"""
Haber kaynagi fetcher - STUB.

Gercek implementasyonda bir haber API'si (ör. NewsAPI, GDELT) veya RSS
kaynaklari kullanilarak Turkce haberler cekilecektir.
"""
from __future__ import annotations


def fetch_news_articles(query: str, limit: int = 5) -> list[dict]:
    """Verilen sorguya gore mock haber makaleleri doner.

    TODO: gercek implementasyonda `requests` ile bir haber API'sine istek
    atilmali ve sonuclar normalize edilmelidir.
    """
    return [
        {
            "id": f"mock-article-{i}",
            "title": f"'{query}' ile ilgili mock haber baslik #{i}",
            "url": f"https://example.com/haber/{i}",
            "source": "MockHaberAjansi",
            "published_at": "2024-01-01T00:00:00Z",
            "summary": f"Bu, '{query}' konusunda otomatik uretilmis bir mock haber ozetidir.",
        }
        for i in range(limit)
    ]
