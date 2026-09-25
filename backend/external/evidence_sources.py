from __future__ import annotations

import hashlib
import logging
from typing import Any

import httpx
from django.conf import settings


logger = logging.getLogger(__name__)


def _stable_id(
    prefix: str,
    value: str,
) -> str:
    digest = hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()[:16]

    return f"{prefix}-{digest}"


class GoogleFactCheckSource:
    """
    Google Fact Check Tools API uzerinden
    daha once fact-check yapilmis claim'leri
    getirir.
    """

    endpoint = (
        "https://factchecktools.googleapis.com/"
        "v1alpha1/claims:search"
    )

    def __init__(
        self,
        *,
        api_key: str | None = None,
        language: str | None = None,
        timeout: float | None = None,
        client: httpx.Client | None = None,
    ):
        self.api_key = (
            settings.GOOGLE_FACT_CHECK_API_KEY
            if api_key is None
            else api_key
        )

        self.language = (
            settings.GOOGLE_FACT_CHECK_LANGUAGE
            if language is None
            else language
        )

        self.timeout = (
            settings.EVIDENCE_HTTP_TIMEOUT_SECONDS
            if timeout is None
            else timeout
        )

        self.client = client

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def _request(
        self,
        params: dict[str, Any],
    ) -> httpx.Response:
        if self.client is not None:
            return self.client.get(
                self.endpoint,
                params=params,
            )

        return httpx.get(
            self.endpoint,
            params=params,
            timeout=self.timeout,
        )

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
    ) -> list[dict]:
        if not self.configured:
            return []

        params: dict[str, Any] = {
            "query": query,
            "pageSize": max(
                1,
                min(limit, 20),
            ),
            "key": self.api_key,
        }

        if self.language:
            params["languageCode"] = (
                self.language
            )

        try:
            response = self._request(
                params
            )

            response.raise_for_status()

        except httpx.HTTPError as exc:
            logger.warning(
                "Google Fact Check request "
                "failed: %s",
                exc,
            )
            return []

        payload = response.json()

        results: list[dict] = []

        for claim in payload.get(
            "claims",
            [],
        ):
            claim_text = str(
                claim.get(
                    "text",
                    "",
                )
            ).strip()

            claimant = str(
                claim.get(
                    "claimant",
                    "",
                )
            ).strip()

            for review in claim.get(
                "claimReview",
                [],
            ):
                url = str(
                    review.get(
                        "url",
                        "",
                    )
                ).strip()

                if not url:
                    continue

                publisher = (
                    review.get(
                        "publisher"
                    )
                    or {}
                )

                rating = str(
                    review.get(
                        "textualRating",
                        "",
                    )
                ).strip()

                summary_parts = []

                if claim_text:
                    summary_parts.append(
                        "Reviewed claim: "
                        f"{claim_text}"
                    )

                if rating:
                    summary_parts.append(
                        f"Rating: {rating}"
                    )

                results.append(
                    {
                        "id": _stable_id(
                            "factcheck",
                            url,
                        ),
                        "title": str(
                            review.get(
                                "title",
                                "",
                            )
                            or claim_text
                        ),
                        "url": url,
                        "source": str(
                            publisher.get(
                                "name",
                                "",
                            )
                            or publisher.get(
                                "site",
                                "",
                            )
                            or "Unknown fact-checker"
                        ),
                        "published_at":
                            review.get(
                                "reviewDate"
                            ),
                        "summary":
                            ". ".join(
                                summary_parts
                            ),
                        "evidence_type":
                            "fact_check",
                        "claim_reviewed":
                            claim_text,
                        "rating": rating,
                        "language": str(
                            review.get(
                                "languageCode",
                                "",
                            )
                        ),
                        "retrieval_source":
                            "google_fact_check",
                        "metadata": {
                            "claimant":
                                claimant,
                            "publisher_site":
                                publisher.get(
                                    "site",
                                    "",
                                ),
                            "claim_date":
                                claim.get(
                                    "claimDate"
                                ),
                        },
                    }
                )

                if len(results) >= limit:
                    return results

        return results


class GDELTNewsSource:
    """
    GDELT DOC 2.0 API ile gercek haber
    URL'leri ve metadata kesfeder.

    Dikkat:
    GDELT sonucu haber iceriginin kendisi
    degildir. Baslik tek basina fact-check
    kaniti olarak kullanilmamalidir.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        timespan: str | None = None,
        timeout: float | None = None,
        client: httpx.Client | None = None,
    ):
        self.base_url = (
            settings.GDELT_DOC_API_URL
            if base_url is None
            else base_url
        )

        self.timespan = (
            settings.GDELT_TIMESPAN
            if timespan is None
            else timespan
        )

        self.timeout = (
            settings.EVIDENCE_HTTP_TIMEOUT_SECONDS
            if timeout is None
            else timeout
        )

        self.client = client

    def _request(
        self,
        params: dict[str, Any],
    ) -> httpx.Response:
        if self.client is not None:
            return self.client.get(
                self.base_url,
                params=params,
            )

        return httpx.get(
            self.base_url,
            params=params,
            timeout=self.timeout,
        )

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
    ) -> list[dict]:
        params = {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": max(
                1,
                min(limit, 250),
            ),
            "sort": "datedesc",
        }

        if self.timespan:
            params["timespan"] = (
                self.timespan
            )

        try:
            response = self._request(
                params
            )

            response.raise_for_status()

        except httpx.HTTPError as exc:
            logger.warning(
                "GDELT request failed: %s",
                exc,
            )
            return []

        payload = response.json()

        results: list[dict] = []

        for article in payload.get(
            "articles",
            [],
        ):
            url = str(
                article.get(
                    "url",
                    "",
                )
            ).strip()

            if not url:
                continue

            results.append(
                {
                    "id": _stable_id(
                        "gdelt",
                        url,
                    ),
                    "title": str(
                        article.get(
                            "title",
                            "",
                        )
                    ),
                    "url": url,
                    "source": str(
                        article.get(
                            "domain",
                            "",
                        )
                        or "Unknown news source"
                    ),
                    "published_at":
                        article.get(
                            "seendate"
                        ),
                    "summary": "",
                    "evidence_type":
                        "news_context",
                    "claim_reviewed": "",
                    "rating": "",
                    "language": str(
                        article.get(
                            "language",
                            "",
                        )
                    ),
                    "retrieval_source":
                        "gdelt",
                    "metadata": {
                        "source_country":
                            article.get(
                                "sourcecountry",
                                "",
                            ),
                    },
                }
            )

            if len(results) >= limit:
                break

        return results
