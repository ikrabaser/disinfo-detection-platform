import httpx

from ai_analysis.evidence_retriever import (
    LiveEvidenceRetriever,
)
from ai_analysis.schemas import Claim
from external.evidence_sources import (
    GDELTNewsSource,
    GoogleFactCheckSource,
)


def test_google_fact_check_skips_without_key():
    source = GoogleFactCheckSource(
        api_key="",
    )

    assert (
        source.search(
            "test claim"
        )
        == []
    )


def test_google_fact_check_normalizes_review():
    def handler(
        request: httpx.Request,
    ):
        assert (
            request.url.params["query"]
            == "Firma X urununu toplatti"
        )

        assert (
            request.url.params["key"]
            == "test-key"
        )

        return httpx.Response(
            200,
            json={
                "claims": [
                    {
                        "text":
                            "Firma X urununu toplatti",
                        "claimant":
                            "Example User",
                        "claimReview": [
                            {
                                "publisher": {
                                    "name":
                                        "Fact Check Org",
                                    "site":
                                        "fact.test",
                                },
                                "url":
                                    "https://fact.test/review",
                                "title":
                                    "Fact check review",
                                "reviewDate":
                                    "2026-09-20T00:00:00Z",
                                "textualRating":
                                    "False",
                                "languageCode":
                                    "tr",
                            }
                        ],
                    }
                ]
            },
        )

    transport = httpx.MockTransport(
        handler
    )

    with httpx.Client(
        transport=transport
    ) as client:
        source = GoogleFactCheckSource(
            api_key="test-key",
            language="tr",
            client=client,
        )

        results = source.search(
            "Firma X urununu toplatti"
        )

    assert len(results) == 1

    result = results[0]

    assert (
        result["evidence_type"]
        == "fact_check"
    )

    assert (
        result["rating"]
        == "False"
    )

    assert (
        result["retrieval_source"]
        == "google_fact_check"
    )


def test_gdelt_normalizes_article():
    def handler(
        request: httpx.Request,
    ):
        assert (
            request.url.params["mode"]
            == "artlist"
        )

        assert (
            request.url.params["format"]
            == "json"
        )

        return httpx.Response(
            200,
            json={
                "articles": [
                    {
                        "url":
                            "https://news.test/article",
                        "title":
                            "Example article",
                        "domain":
                            "news.test",
                        "seendate":
                            "20260925T120000Z",
                        "language":
                            "Turkish",
                        "sourcecountry":
                            "Turkey",
                    }
                ]
            },
        )

    transport = httpx.MockTransport(
        handler
    )

    with httpx.Client(
        transport=transport
    ) as client:
        source = GDELTNewsSource(
            client=client,
            timespan="3months",
        )

        results = source.search(
            "test claim"
        )

    assert len(results) == 1

    result = results[0]

    assert (
        result["evidence_type"]
        == "news_context"
    )

    assert (
        result["source"]
        == "news.test"
    )

    assert (
        result["retrieval_source"]
        == "gdelt"
    )


def test_live_retriever_prioritizes_fact_check_and_deduplicates():
    class FakeFactCheckSource:
        def search(
            self,
            query,
            *,
            limit,
        ):
            return [
                {
                    "id": "fc-1",
                    "title": "Fact check",
                    "url":
                        "https://same.test/item",
                    "source": "Fact",
                    "summary":
                        "Reviewed claim. Rating: False",
                    "evidence_type":
                        "fact_check",
                    "rating": "False",
                    "retrieval_source":
                        "google_fact_check",
                }
            ]

    class FakeNewsSource:
        def search(
            self,
            query,
            *,
            limit,
        ):
            return [
                {
                    "id": "news-1",
                    "title":
                        "Duplicate article",
                    "url":
                        "https://same.test/item",
                    "source": "News",
                    "evidence_type":
                        "news_context",
                    "retrieval_source":
                        "gdelt",
                },
                {
                    "id": "news-2",
                    "title":
                        "Independent article",
                    "url":
                        "https://news.test/2",
                    "source": "News",
                    "evidence_type":
                        "news_context",
                    "retrieval_source":
                        "gdelt",
                },
            ]

    retriever = LiveEvidenceRetriever(
        fact_check_source=
            FakeFactCheckSource(),
        news_source=
            FakeNewsSource(),
    )

    evidence = retriever.retrieve(
        Claim(
            id="claim-1",
            text="Test claim",
        ),
        limit=5,
    )

    assert len(evidence) == 2

    assert (
        evidence[0].evidence_type
        == "fact_check"
    )

    assert (
        evidence[1].evidence_type
        == "news_context"
    )
