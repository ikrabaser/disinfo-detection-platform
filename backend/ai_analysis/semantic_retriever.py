from __future__ import annotations

from dataclasses import (
    asdict,
    dataclass,
)

from django.conf import settings
from pgvector.django import (
    CosineDistance,
)

from ai_analysis.embeddings import (
    EmbeddingProvider,
    OpenAIEmbeddingProvider,
)
from ai_analysis.models import (
    EvidenceChunk,
)


@dataclass(slots=True)
class SemanticMatch:
    chunk_id: int
    document_id: int
    chunk_index: int
    text: str
    url: str
    title: str
    source: str
    similarity: float

    def to_dict(self) -> dict:
        return asdict(self)


class SemanticChunkRetriever:
    def __init__(
        self,
        *,
        embedding_provider:
            EmbeddingProvider | None = None,
    ):
        self.embedding_provider = (
            embedding_provider
            or OpenAIEmbeddingProvider()
        )

    def search(
        self,
        query: str,
        *,
        top_k: int | None = None,
        min_similarity:
            float | None = None,
        document_ids:
            list[int] | None = None,
    ) -> list[SemanticMatch]:
        normalized = query.strip()

        if not normalized:
            return []

        top_k = (
            settings.RAG_TOP_K
            if top_k is None
            else top_k
        )

        min_similarity = (
            settings.RAG_MIN_SIMILARITY
            if min_similarity is None
            else min_similarity
        )

        query_vector = (
            self.embedding_provider.embed(
                [normalized]
            )[0]
        )

        queryset = (
            EvidenceChunk.objects
            .select_related(
                "document"
            )
        )

        if document_ids is not None:
            if not document_ids:
                return []

            queryset = queryset.filter(
                document_id__in=document_ids
            )

        queryset = (
            queryset
            .annotate(
                distance=CosineDistance(
                    "embedding",
                    query_vector,
                )
            )
            .order_by(
                "distance"
            )
        )

        matches: list[
            SemanticMatch
        ] = []

        for chunk in queryset[
            :max(top_k * 3, top_k)
        ]:
            similarity = (
                1.0
                - float(
                    chunk.distance
                )
            )

            if (
                similarity
                < min_similarity
            ):
                continue

            matches.append(
                SemanticMatch(
                    chunk_id=chunk.id,
                    document_id=(
                        chunk.document_id
                    ),
                    chunk_index=(
                        chunk.chunk_index
                    ),
                    text=chunk.text,
                    url=(
                        chunk.document.url
                    ),
                    title=(
                        chunk.document.title
                    ),
                    source=(
                        chunk.document.source
                    ),
                    similarity=round(
                        similarity,
                        6,
                    ),
                )
            )

            if len(matches) >= top_k:
                break

        return matches
