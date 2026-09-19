"""
X (Twitter) API istemcisi - STUB.

ONEMLI: Bu modul GERCEK bir X API cagrisi YAPMAZ. `get_x_api_client()`
gercek kullanimda `tweepy` veya dogrudan `requests` ile X API v2'ye baglanacak
bir istemci dondurmelidir; burada sadece arayuz (interface) ve mock veri
saglanmistir.

TODO (gercek implementasyon):
    import tweepy
    client = tweepy.Client(bearer_token=settings.X_API_BEARER_TOKEN)
    return client
"""
from __future__ import annotations

from django.conf import settings


class MockXAPIClient:
    """X API istemcisinin gercek olmayan (mock) implementasyonu."""

    def __init__(self, bearer_token: str):
        self.bearer_token = bearer_token

    def search_recent_posts(self, query: str, max_results: int = 10) -> list[dict]:
        """Verilen sorguya gore mock paylasim listesi doner.

        TODO: gercek implementasyonda `client.search_recent_tweets(query=query,
        max_results=max_results)` gibi bir cagri yapilmalidir.
        """
        return [
            {
                "id": f"mock-post-{i}",
                "author_id": f"mock-user-{i % 3}",
                "text": f"'{query}' hakkinda mock paylasim #{i}",
                "created_at": "2024-01-01T00:00:00Z",
                "shared_from_id": f"mock-post-{i - 1}" if i > 0 else None,
                "like_count": 10 * i,
                "retweet_count": 2 * i,
            }
            for i in range(max_results)
        ]

    def get_user(self, user_id: str) -> dict:
        """Mock kullanici profili doner (bot analizi icin ozellikler dahil)."""
        return {
            "id": user_id,
            "username": f"user_{user_id}",
            "followers_count": 42,
            "following_count": 100,
            "account_age_days": 365,
            "verified": False,
        }


def get_x_api_client() -> MockXAPIClient:
    """X API istemcisini env degiskenlerinden yapilandirip doner (STUB).

    `settings.X_API_BEARER_TOKEN` bos ise bile mock istemci calismaya devam
    eder - boylece gelistirme ortaminda gercek API anahtari olmadan da
    sistem uctan uca test edilebilir.
    """
    bearer_token = settings.X_API_BEARER_TOKEN
    # TODO: bearer_token bos degilse gercek tweepy.Client dondur.
    return MockXAPIClient(bearer_token=bearer_token)
