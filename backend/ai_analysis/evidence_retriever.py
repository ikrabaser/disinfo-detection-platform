from __future__ import annotations

from abc import ABC, abstractmethod

from ai_analysis.schemas import (
    Claim,
    EvidenceItem,
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


class NewsEvidenceRetriever(
    EvidenceRetriever
):
    """
    Ilk retrieval implementasyonu.

    Su an external.news_fetcher kullanir.
    Daha sonra ayni interface altinda
    semantic/vector RAG implementasyonu
    eklenebilir.
    """

    mode = "news-search"

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

        evidence: list[
            EvidenceItem
        ] = []

        for index, article in enumerate(
            articles,
            start=1,
        ):
            evidence.append(
                EvidenceItem(
                    id=str(
                        article.get(
                            "id",
                            (
                                f"{claim.id}"
                                f"-evidence-{index}"
                            ),
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
                )
            )

        return evidence
