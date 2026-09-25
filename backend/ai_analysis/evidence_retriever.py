from __future__ import annotations

from abc import ABC, abstractmethod

from ai_analysis.schemas import (
    Claim,
    EvidenceItem,
)
from external.article_fetcher import (
    ArticleContentFetcher,
    ArticleFetchError,
    UnsafeArticleURLError,
)
from external.evidence_sources import (
    GDELTNewsSource,
    GoogleFactCheckSource,
)
from external.news_fetcher import (
    fetch_news_articles,
)


class EvidenceRetriever(ABC):
    mode = "unknown"

    @abstractmethod
    def retrieve(
        self,
        claim: Claim,
        *,
        limit: int = 5,
    ) -> list[EvidenceItem]:
        pass


def _to_evidence_item(
    raw: dict,
) -> EvidenceItem:
    return EvidenceItem(
        id=str(
            raw.get(
                "id",
                "",
            )
        ),
        title=str(
            raw.get(
                "title",
                "",
            )
        ),
        url=str(
            raw.get(
                "url",
                "",
            )
        ),
        source=str(
            raw.get(
                "source",
                "unknown",
            )
        ),
        published_at=raw.get(
            "published_at"
        ),
        summary=str(
            raw.get(
                "summary",
                "",
            )
        ),
        content=str(
            raw.get(
                "content",
                "",
            )
        ),
        content_status=str(
            raw.get(
                "content_status",
                "not_fetched",
            )
        ),
        evidence_type=str(
            raw.get(
                "evidence_type",
                "unknown",
            )
        ),
        claim_reviewed=str(
            raw.get(
                "claim_reviewed",
                "",
            )
        ),
        rating=str(
            raw.get(
                "rating",
                "",
            )
        ),
        language=str(
            raw.get(
                "language",
                "",
            )
        ),
        retrieval_source=str(
            raw.get(
                "retrieval_source",
                "",
            )
        ),
        metadata=dict(
            raw.get(
                "metadata"
            )
            or {}
        ),
    )


class LiveEvidenceRetriever(
    EvidenceRetriever
):
    """
    Production evidence discovery.

    1. Google Fact Check
    2. GDELT news discovery
    3. Haber URL'sinden guvenli content fetch

    Ayni URL birden fazla kaynaktan gelirse
    tek evidence kaydi tutulur.
    """

    mode = (
        "google-fact-check+gdelt"
    )

    def __init__(
        self,
        *,
        fact_check_source=None,
        news_source=None,
        article_fetcher=None,
    ):
        self.fact_check_source = (
            fact_check_source
            if fact_check_source
            is not None
            else GoogleFactCheckSource()
        )

        self.news_source = (
            news_source
            if news_source
            is not None
            else GDELTNewsSource()
        )

        self.article_fetcher = (
            article_fetcher
            if article_fetcher
            is not None
            else ArticleContentFetcher()
        )

    def _enrich_news_context(
        self,
        item: EvidenceItem,
    ) -> None:
        try:
            document = (
                self.article_fetcher.fetch(
                    item.url
                )
            )

        except (
            ArticleFetchError,
            UnsafeArticleURLError,
        ) as exc:
            item.content_status = (
                "unavailable"
            )

            item.metadata[
                "content_error"
            ] = str(exc)

            return

        item.content = (
            document.content
        )

        item.content_status = (
            "fetched"
        )

        item.metadata.update(
            {
                "final_url":
                    document.final_url,
                "extracted_title":
                    document.title,
                "content_type":
                    document.content_type,
            }
        )

    def retrieve(
        self,
        claim: Claim,
        *,
        limit: int = 5,
    ) -> list[EvidenceItem]:
        if limit <= 0:
            return []

        candidates: list[dict] = []

        fact_checks = (
            self.fact_check_source.search(
                claim.text,
                limit=min(
                    limit,
                    3,
                ),
            )
        )

        candidates.extend(
            fact_checks
        )

        if len(candidates) < limit:
            news_results = (
                self.news_source.search(
                    claim.text,
                    limit=limit,
                )
            )

            candidates.extend(
                news_results
            )

        evidence: list[
            EvidenceItem
        ] = []

        seen_urls: set[str] = set()

        for raw in candidates:
            url = str(
                raw.get(
                    "url",
                    "",
                )
            ).strip()

            if not url:
                continue

            if url in seen_urls:
                continue

            seen_urls.add(
                url
            )

            item = _to_evidence_item(
                raw
            )

            if (
                item.evidence_type
                == "news_context"
            ):
                self._enrich_news_context(
                    item
                )

            evidence.append(
                item
            )

            if len(evidence) >= limit:
                break

        return evidence


class NewsEvidenceRetriever(
    EvidenceRetriever
):
    """
    Legacy development retriever.

    MOCK news_fetcher kullanir.
    Production orchestrator tarafindan
    default olarak kullanilmaz.
    """

    mode = "mock-news-search"

    def retrieve(
        self,
        claim: Claim,
        *,
        limit: int = 5,
    ) -> list[EvidenceItem]:
        articles = fetch_news_articles(
            query=claim.text,
            limit=limit,
        )

        return [
            EvidenceItem(
                id=str(
                    article.get(
                        "id",
                        "",
                    )
                ),
                title=str(
                    article.get(
                        "title",
                        "",
                    )
                ),
                url=str(
                    article.get(
                        "url",
                        "",
                    )
                ),
                source=str(
                    article.get(
                        "source",
                        "unknown",
                    )
                ),
                published_at=(
                    article.get(
                        "published_at"
                    )
                ),
                summary=str(
                    article.get(
                        "summary",
                        "",
                    )
                ),
                evidence_type="mock",
                retrieval_source=(
                    "mock_news_fetcher"
                ),
            )
            for article in articles
        ]
