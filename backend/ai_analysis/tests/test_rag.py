from types import SimpleNamespace

import pytest

from ai_analysis.chunking import (
    TokenChunker,
)
from ai_analysis.embeddings import (
    OpenAIEmbeddingProvider,
)
from ai_analysis.indexer import (
    EvidenceIndexer,
)
from ai_analysis.models import (
    EvidenceChunk,
    EvidenceDocument,
)
from ai_analysis.schemas import (
    EvidenceItem,
)
from ai_analysis.semantic_retriever import (
    SemanticChunkRetriever,
)


DIMENSIONS = 1536


class FakeEmbeddingProvider:
    model = "fake-embedding"

    def embed(
        self,
        texts,
    ):
        return [
            [
                0.5
                for _ in range(
                    DIMENSIONS
                )
            ]
            for _ in texts
        ]


def test_chunker_short_text():
    chunker = TokenChunker(
        max_tokens=50,
        overlap=10,
    )

    chunks = chunker.chunk(
        "Kisa bir kanit metni."
    )

    assert len(chunks) == 1
    assert chunks[0].token_count <= 50


def test_chunker_splits_long_text():
    chunker = TokenChunker(
        max_tokens=20,
        overlap=5,
    )

    text = (
        "evidence "
        * 100
    )

    chunks = chunker.chunk(
        text
    )

    assert len(chunks) > 1

    assert all(
        chunk.token_count <= 20
        for chunk in chunks
    )


def test_openai_embedding_provider_maps_vectors():
    class FakeEmbeddings:
        def create(
            self,
            **kwargs,
        ):
            assert (
                kwargs["model"]
                == "test-embedding"
            )

            return SimpleNamespace(
                data=[
                    SimpleNamespace(
                        index=0,
                        embedding=[
                            0.25
                        ] * DIMENSIONS,
                    )
                ]
            )

    client = SimpleNamespace(
        embeddings=FakeEmbeddings()
    )

    provider = (
        OpenAIEmbeddingProvider(
            api_key="test",
            model="test-embedding",
            dimensions=DIMENSIONS,
            client=client,
        )
    )

    result = provider.embed(
        ["test"]
    )

    assert len(result) == 1

    assert (
        len(result[0])
        == DIMENSIONS
    )


@pytest.mark.django_db
def test_indexer_creates_document_and_chunks():
    indexer = EvidenceIndexer(
        embedding_provider=(
            FakeEmbeddingProvider()
        ),
        chunker=TokenChunker(
            max_tokens=20,
            overlap=5,
        ),
    )

    evidence = EvidenceItem(
        id="e-1",
        title="Test article",
        url=(
            "https://example.test/"
            "article"
        ),
        source="Example",
        content=(
            "Bu bir test evidence "
            "icerigidir. "
            * 30
        ),
        content_status="fetched",
        evidence_type="news_context",
        retrieval_source="gdelt",
    )

    result = indexer.index(
        evidence
    )

    assert result.indexed is True

    assert (
        EvidenceDocument.objects.count()
        == 1
    )

    assert (
        EvidenceChunk.objects.count()
        > 1
    )


@pytest.mark.django_db
def test_indexer_skips_unchanged_content():
    indexer = EvidenceIndexer(
        embedding_provider=(
            FakeEmbeddingProvider()
        ),
        chunker=TokenChunker(
            max_tokens=50,
            overlap=10,
        ),
    )

    evidence = EvidenceItem(
        id="e-2",
        title="Same article",
        url=(
            "https://example.test/"
            "same"
        ),
        source="Example",
        content=(
            "Degismeyen evidence "
            "icerigi."
        ),
        content_status="fetched",
    )

    first = indexer.index(
        evidence
    )

    second = indexer.index(
        evidence
    )

    assert first.indexed is True

    assert second.indexed is False

    assert (
        second.reason
        == "Content degismedi."
    )


@pytest.mark.django_db
def test_semantic_retriever_orders_by_cosine():
    document = (
        EvidenceDocument.objects.create(
            url=(
                "https://example.test/"
                "semantic"
            ),
            title="Semantic Test",
            source="Example",
            content="test",
            content_hash="abc",
        )
    )

    vector_a = (
        [1.0]
        + [0.0] * (
            DIMENSIONS - 1
        )
    )

    vector_b = (
        [0.0, 1.0]
        + [0.0] * (
            DIMENSIONS - 2
        )
    )

    EvidenceChunk.objects.create(
        document=document,
        chunk_index=0,
        text="closest chunk",
        token_count=2,
        embedding_model="fake",
        embedding=vector_a,
    )

    EvidenceChunk.objects.create(
        document=document,
        chunk_index=1,
        text="other chunk",
        token_count=2,
        embedding_model="fake",
        embedding=vector_b,
    )

    class QueryEmbeddingProvider:
        model = "fake"

        def embed(
            self,
            texts,
        ):
            return [
                vector_a
            ]

    retriever = (
        SemanticChunkRetriever(
            embedding_provider=(
                QueryEmbeddingProvider()
            )
        )
    )

    matches = retriever.search(
        "query",
        top_k=2,
        min_similarity=-1.0,
    )

    assert (
        matches[0].text
        == "closest chunk"
    )

    assert (
        matches[0].similarity
        > matches[1].similarity
    )
