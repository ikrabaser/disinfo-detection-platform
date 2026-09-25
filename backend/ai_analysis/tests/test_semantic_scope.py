from __future__ import annotations

import pytest

from ai_analysis.models import (
    EvidenceChunk,
    EvidenceDocument,
)
from ai_analysis.semantic_retriever import (
    SemanticChunkRetriever,
)


class FakeEmbeddingProvider:
    model = "fake-embedding"

    def embed(
        self,
        texts,
    ):
        vector = [
            0.0
            for _ in range(1536)
        ]

        vector[0] = 1.0

        return [
            vector
            for _ in texts
        ]


@pytest.mark.django_db
def test_semantic_search_respects_document_scope():
    document_a = (
        EvidenceDocument.objects.create(
            url="https://example.com/a",
            title="A",
            source="Example",
            content="A content",
            content_hash="a" * 64,
        )
    )

    document_b = (
        EvidenceDocument.objects.create(
            url="https://example.com/b",
            title="B",
            source="Example",
            content="B content",
            content_hash="b" * 64,
        )
    )

    vector = [
        0.0
        for _ in range(1536)
    ]

    vector[0] = 1.0

    EvidenceChunk.objects.create(
        document=document_a,
        chunk_index=0,
        text="Document A evidence",
        token_count=3,
        embedding_model="fake",
        embedding=vector,
    )

    EvidenceChunk.objects.create(
        document=document_b,
        chunk_index=0,
        text="Document B evidence",
        token_count=3,
        embedding_model="fake",
        embedding=vector,
    )

    retriever = (
        SemanticChunkRetriever(
            embedding_provider=
                FakeEmbeddingProvider()
        )
    )

    matches = retriever.search(
        "test query",
        top_k=5,
        min_similarity=0.0,
        document_ids=[
            document_a.id
        ],
    )

    assert matches

    assert {
        item.document_id
        for item in matches
    } == {
        document_a.id
    }
