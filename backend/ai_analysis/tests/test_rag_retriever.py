from ai_analysis.embeddings import (
    EmbeddingConfigurationError,
)
from ai_analysis.indexer import (
    IndexResult,
)
from ai_analysis.rag_retriever import (
    RAGEvidenceRetriever,
)
from ai_analysis.schemas import (
    Claim,
    EvidenceItem,
)
from ai_analysis.semantic_retriever import (
    SemanticMatch,
)


class FakeLiveRetriever:
    def retrieve(
        self,
        claim,
        *,
        limit,
    ):
        return [
            EvidenceItem(
                id="fact-1",
                title="Fact check",
                url=(
                    "https://fact.test/1"
                ),
                source="FactCheck",
                summary="Rating: False",
                evidence_type="fact_check",
                rating="False",
                retrieval_source=(
                    "google_fact_check"
                ),
            ),
            EvidenceItem(
                id="news-1",
                title="News article",
                url=(
                    "https://news.test/1"
                ),
                source="News",
                content=(
                    "Makalenin tam icerigi "
                    "burada bulunuyor."
                ),
                content_status="fetched",
                evidence_type=(
                    "news_context"
                ),
                retrieval_source="gdelt",
            ),
        ]


class FakeIndexer:
    def index(
        self,
        evidence,
    ):
        assert (
            evidence.evidence_type
            == "news_context"
        )

        return IndexResult(
            document_id=17,
            created=True,
            indexed=True,
            chunk_count=2,
        )


class FakeSemanticRetriever:
    def search(
        self,
        query,
        *,
        top_k,
        min_similarity,
        document_ids,
    ):
        assert (
            document_ids
            == [17]
        )

        return [
            SemanticMatch(
                chunk_id=101,
                document_id=17,
                chunk_index=0,
                text=(
                    "Claim ile ilgili "
                    "en alakali kanit."
                ),
                url=(
                    "https://news.test/1"
                ),
                title="News article",
                source="News",
                similarity=0.82,
            )
        ]


def test_rag_retriever_returns_fact_check_and_semantic_chunk(
    settings,
):
    settings.RAG_MIN_SIMILARITY = 0.35

    retriever = (
        RAGEvidenceRetriever(
            live_retriever=
                FakeLiveRetriever(),
            indexer=FakeIndexer(),
            semantic_retriever=
                FakeSemanticRetriever(),
        )
    )

    result = retriever.retrieve(
        Claim(
            id="claim-1",
            text="Test claim",
        ),
        limit=5,
    )

    assert len(result) == 2

    assert (
        result[0].evidence_type
        == "fact_check"
    )

    assert (
        result[1].evidence_type
        == "rag_chunk"
    )

    assert (
        result[1].metadata[
            "similarity"
        ]
        == 0.82
    )


def test_rag_retriever_degrades_when_embedding_fails(
    settings,
):
    settings.RAG_MIN_SIMILARITY = 0.35

    class FailingIndexer:
        def index(
            self,
            evidence,
        ):
            raise (
                EmbeddingConfigurationError(
                    "Embedding unavailable"
                )
            )

    retriever = (
        RAGEvidenceRetriever(
            live_retriever=
                FakeLiveRetriever(),
            indexer=FailingIndexer(),
            semantic_retriever=
                FakeSemanticRetriever(),
        )
    )

    result = retriever.retrieve(
        Claim(
            id="claim-1",
            text="Test claim",
        ),
        limit=5,
    )

    assert len(result) == 2

    assert (
        result[0].evidence_type
        == "fact_check"
    )

    assert (
        result[1].evidence_type
        == "news_context"
    )
