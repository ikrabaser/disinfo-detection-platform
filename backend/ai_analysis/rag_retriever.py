from __future__ import annotations

from django.conf import settings
from django.db import DatabaseError

from ai_analysis.embeddings import (
    EmbeddingError,
)
from ai_analysis.evidence_retriever import (
    EvidenceRetriever,
    LiveEvidenceRetriever,
)
from ai_analysis.indexer import (
    EvidenceIndexer,
)
from ai_analysis.schemas import (
    Claim,
    EvidenceItem,
)
from ai_analysis.semantic_retriever import (
    SemanticChunkRetriever,
)


class RAGEvidenceRetriever(
    EvidenceRetriever
):
    """
    VERITAS grounded RAG retrieval.

    Akis:
        live source discovery
        -> article fetch
        -> chunk/index
        -> pgvector semantic retrieval
        -> grounded evidence chunks
    """

    mode = (
        "google-fact-check"
        "+gdelt"
        "+pgvector-rag"
    )

    def __init__(
        self,
        *,
        live_retriever=None,
        indexer=None,
        semantic_retriever=None,
    ):
        self.live_retriever = (
            live_retriever
            if live_retriever is not None
            else LiveEvidenceRetriever()
        )

        self.indexer = (
            indexer
            if indexer is not None
            else EvidenceIndexer()
        )

        self.semantic_retriever = (
            semantic_retriever
            if semantic_retriever is not None
            else SemanticChunkRetriever()
        )

    def _fallback(
        self,
        evidence: list[EvidenceItem],
    ) -> list[EvidenceItem]:
        """
        Embedding/vector katmani kullanilamazsa
        fact-check ve fetch edilmis article
        evidence ile sistem calismaya devam eder.
        """

        return [
            item
            for item in evidence
            if (
                item.evidence_type
                == "fact_check"
                or (
                    item.evidence_type
                    == "news_context"
                    and item.content_status
                    == "fetched"
                    and bool(item.content)
                )
            )
        ]

    def retrieve(
        self,
        claim: Claim,
        *,
        limit: int = 5,
    ) -> list[EvidenceItem]:
        if limit <= 0:
            return []

        discovered = (
            self.live_retriever.retrieve(
                claim,
                limit=limit,
            )
        )

        fact_checks = [
            item
            for item in discovered
            if (
                item.evidence_type
                == "fact_check"
            )
        ]

        indexable = [
            item
            for item in discovered
            if (
                item.evidence_type
                == "news_context"
                and item.content_status
                == "fetched"
                and bool(item.content)
            )
        ]

        if not indexable:
            return fact_checks

        document_ids: list[int] = []

        try:
            for item in indexable:
                result = (
                    self.indexer.index(
                        item
                    )
                )

                if result.document_id:
                    document_ids.append(
                        result.document_id
                    )

            if not document_ids:
                return self._fallback(
                    discovered
                )

            remaining = max(
                1,
                limit - len(
                    fact_checks
                ),
            )

            matches = (
                self.semantic_retriever
                .search(
                    claim.text,
                    top_k=remaining,
                    min_similarity=(
                        settings
                        .RAG_MIN_SIMILARITY
                    ),
                    document_ids=(
                        document_ids
                    ),
                )
            )

        except (
            EmbeddingError,
            DatabaseError,
        ):
            return self._fallback(
                discovered
            )

        rag_items = [
            EvidenceItem(
                id=(
                    f"rag-chunk-"
                    f"{match.chunk_id}"
                ),
                title=match.title,
                url=match.url,
                source=match.source,
                content=match.text,
                content_status="fetched",
                evidence_type="rag_chunk",
                retrieval_source=(
                    "pgvector"
                ),
                metadata={
                    "document_id":
                        match.document_id,
                    "chunk_id":
                        match.chunk_id,
                    "chunk_index":
                        match.chunk_index,
                    "similarity":
                        match.similarity,
                },
            )
            for match in matches
        ]

        if not rag_items:
            return self._fallback(
                discovered
            )

        return (
            fact_checks
            + rag_items
        )[:limit]
