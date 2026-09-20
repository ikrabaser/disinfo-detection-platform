"""
X API v2 istemcisi.

Bearer token varsa gerçek X API kullanılır.
Token yoksa geliştirme ortamı için mock client'a düşülür.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx
from django.conf import settings


class XAPIError(RuntimeError):
    """X API çağrılarında oluşan kontrollü hata."""


class XAPIClient:
    def __init__(
        self,
        bearer_token: str,
        base_url: str = "https://api.x.com/2",
        timeout: float = 20.0,
    ):
        if not bearer_token:
            raise ValueError("X_API_BEARER_TOKEN tanımlı değil.")

        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self.headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Accept": "application/json",
            "User-Agent": "veritas-disinfo-platform/0.1",
        }

    def _get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"

        try:
            with httpx.Client(
                headers=self.headers,
                timeout=self.timeout,
            ) as client:
                response = client.get(url, params=params)

            response.raise_for_status()

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code

            try:
                detail = exc.response.json()
            except Exception:
                detail = exc.response.text

            raise XAPIError(
                f"X API HTTP {status_code}: {detail}"
            ) from exc

        except httpx.RequestError as exc:
            raise XAPIError(
                f"X API bağlantı hatası: {exc}"
            ) from exc

        return response.json()

    def search_recent_posts(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Son X paylaşımlarını arar.

        X API recent search endpoint'i minimum 10 sonuç parametresi beklediği
        için max_results 10-100 aralığına sınırlandırılır.
        """

        query = query.strip()

        if not query:
            raise ValueError("Arama sorgusu boş olamaz.")

        max_results = max(10, min(max_results, 100))

        payload = self._get(
            "/tweets/search/recent",
            params={
                "query": query,
                "max_results": max_results,
                "tweet.fields": ",".join(
                    [
                        "id",
                        "text",
                        "author_id",
                        "created_at",
                        "conversation_id",
                        "lang",
                        "public_metrics",
                        "referenced_tweets",
                    ]
                ),
                "expansions": "author_id",
                "user.fields": ",".join(
                    [
                        "id",
                        "name",
                        "username",
                        "created_at",
                        "verified",
                        "public_metrics",
                    ]
                ),
            },
        )

        users = {
            user["id"]: user
            for user in payload.get("includes", {}).get("users", [])
        }

        results: list[dict[str, Any]] = []

        for post in payload.get("data", []):
            metrics = post.get("public_metrics") or {}
            author = users.get(post.get("author_id"), {})

            shared_from_id = None
            reference_type = None

            references = post.get("referenced_tweets") or []

            if references:
                reference = references[0]
                shared_from_id = reference.get("id")
                reference_type = reference.get("type")

            author_metrics = author.get("public_metrics") or {}

            results.append(
                {
                    "id": post.get("id"),
                    "author_id": post.get("author_id"),
                    "author_username": author.get("username"),
                    "author_name": author.get("name"),
                    "text": post.get("text"),
                    "created_at": post.get("created_at"),
                    "conversation_id": post.get("conversation_id"),
                    "lang": post.get("lang"),
                    "shared_from_id": shared_from_id,
                    "reference_type": reference_type,
                    "like_count": metrics.get("like_count", 0),
                    "retweet_count": metrics.get("retweet_count", 0),
                    "reply_count": metrics.get("reply_count", 0),
                    "quote_count": metrics.get("quote_count", 0),
                    "author_followers_count": author_metrics.get(
                        "followers_count", 0
                    ),
                    "author_following_count": author_metrics.get(
                        "following_count", 0
                    ),
                    "author_post_count": author_metrics.get(
                        "tweet_count", 0
                    ),
                    "author_verified": author.get("verified", False),
                }
            )

        return results

    def get_user(self, user_id: str) -> dict[str, Any]:
        payload = self._get(
            f"/users/{user_id}",
            params={
                "user.fields": ",".join(
                    [
                        "id",
                        "name",
                        "username",
                        "created_at",
                        "verified",
                        "public_metrics",
                    ]
                )
            },
        )

        user = payload.get("data") or {}
        metrics = user.get("public_metrics") or {}

        account_age_days = None
        created_at = user.get("created_at")

        if created_at:
            created = datetime.fromisoformat(
                created_at.replace("Z", "+00:00")
            )
            account_age_days = (
                datetime.now(timezone.utc) - created
            ).days

        return {
            "id": user.get("id"),
            "username": user.get("username"),
            "name": user.get("name"),
            "created_at": created_at,
            "account_age_days": account_age_days,
            "followers_count": metrics.get("followers_count", 0),
            "following_count": metrics.get("following_count", 0),
            "post_count": metrics.get("tweet_count", 0),
            "listed_count": metrics.get("listed_count", 0),
            "verified": user.get("verified", False),
        }


class MockXAPIClient:
    """
    X API anahtarı olmadan geliştirme yapmak için mock client.
    """

    def __init__(self, bearer_token: str = ""):
        self.bearer_token = bearer_token

    def _mock_text(self, query: str, index: int) -> str:
        templates = [
            f"{query} hakkında resmi kaynaklardan açıklama yayımlandı.",
            f"ŞOK!!! {query} konusunda inanılmaz gelişme, paylaşmadan geçme!",
            f"{query} hakkında inanılmaz bir iddia sosyal medyada gündemde.",
            f"{query} ile ilgili doğrulama çalışmaları devam ediyor.",
        ]
        return templates[index % len(templates)]

    def search_recent_posts(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        return [
            {
                "id": f"mock-post-{i}",
                "author_id": f"mock-user-{i % 3}",
                "author_username": f"mock_user_{i % 3}",
                "author_name": f"Mock User {i % 3}",
                "text": self._mock_text(query, i),
                "created_at": "2026-09-20T09:00:00Z",
                "conversation_id": "mock-conversation",
                "lang": "tr",
                "shared_from_id": (
                    f"mock-post-{i - 1}" if i > 0 else None
                ),
                "reference_type": (
                    "retweeted" if i > 0 else None
                ),
                "like_count": 10 * i,
                "retweet_count": 2 * i,
                "reply_count": i,
                "quote_count": 0,
                "author_followers_count": 100 + i,
                "author_following_count": 50,
                "author_post_count": 1000,
                "author_verified": False,
            }
            for i in range(max_results)
        ]

    def get_user(self, user_id: str) -> dict[str, Any]:
        return {
            "id": user_id,
            "username": f"user_{user_id}",
            "name": "Mock User",
            "created_at": "2025-01-01T00:00:00Z",
            "account_age_days": 600,
            "followers_count": 42,
            "following_count": 100,
            "post_count": 500,
            "listed_count": 0,
            "verified": False,
        }


def get_x_api_client():
    """
    Token varsa gerçek X API client'ı, yoksa mock client döndürür.
    """

    bearer_token = settings.X_API_BEARER_TOKEN.strip()

    if not bearer_token:
        return MockXAPIClient()

    return XAPIClient(
        bearer_token=bearer_token,
        base_url=settings.X_API_BASE_URL,
    )
