from __future__ import annotations

import hashlib
from dataclasses import dataclass

from django.db import transaction

from ai_analysis.chunking import (
    TokenChunker,
)
from ai_analysis.embeddings import (
    EmbeddingProvider,
    OpenAIEmbeddingProvider,
)
from ai_analysis.models import (
    EvidenceChunk,
    EvidenceDocument,
)
from ai_analysis.schemas import (
    EvidenceItem,
)


@dataclass(slots=True)
class IndexResult:
    document_id: int | None
    created: bool
    indexed: bool
    chunk_count: int
    reason: str = ""


def content_hash(
    content: str,
) -> str:
    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


class EvidenceIndexer:
    def __init__(
        self,
        *,
        embedding_provider:
            EmbeddingProvider | None = None,
        chunker:
            TokenChunker | None = None,
    ):
        self.embedding_provider = (
            embedding_provider
            or OpenAIEmbeddingProvider()
        )

        self.chunker = (
            chunker
            or TokenChunker()
        )

    @transaction.atomic
    def index(
        self,
        evidence: EvidenceItem,
    ) -> IndexResult:
        content = (
            evidence.content
            or ""
        ).strip()

        if (
            evidence.content_status
            != "fetched"
            or not content
        ):
            return IndexResult(
                document_id=None,
                created=False,
                indexed=False,
                chunk_count=0,
                reason=(
                    "Evidence content "
                    "kullanilabilir degil."
                ),
            )

        digest = content_hash(
            content
        )

        document, created = (
            EvidenceDocument.objects
            .get_or_create(
                url=evidence.url,
                defaults={
                    "title":
                        evidence.title,
                    "source":
                        evidence.source,
                    "language":
                        evidence.language,
                    "retrieval_source":
                        evidence.retrieval_source,
                    "content":
                        content,
                    "content_hash":
                        digest,
                    "metadata":
                        evidence.metadata,
                },
            )
        )

        if (
            not created
            and document.content_hash
            == digest
            and document.chunks.exists()
        ):
            return IndexResult(
                document_id=document.id,
                created=False,
                indexed=False,
                chunk_count=(
                    document.chunks.count()
                ),
                reason=(
                    "Content degismedi."
                ),
            )

        document.title = (
            evidence.title
        )

        document.source = (
            evidence.source
        )

        document.language = (
            evidence.language
        )

        document.retrieval_source = (
            evidence.retrieval_source
        )

        document.content = content

        document.content_hash = (
            digest
        )

        document.metadata = (
            evidence.metadata
        )

        document.save()

        chunks = self.chunker.chunk(
            content
        )

        if not chunks:
            return IndexResult(
                document_id=document.id,
                created=created,
                indexed=False,
                chunk_count=0,
                reason=(
                    "Chunk olusturulamadi."
                ),
            )

        vectors = (
            self.embedding_provider.embed(
                [
                    chunk.text
                    for chunk in chunks
                ]
            )
        )

        document.chunks.all().delete()

        EvidenceChunk.objects.bulk_create(
            [
                EvidenceChunk(
                    document=document,
                    chunk_index=(
                        chunk.index
                    ),
                    text=chunk.text,
                    token_count=(
                        chunk.token_count
                    ),
                    embedding_model=(
                        self.embedding_provider
                        .model
                    ),
                    embedding=vector,
                )
                for chunk, vector
                in zip(
                    chunks,
                    vectors,
                    strict=True,
                )
            ]
        )

        return IndexResult(
            document_id=document.id,
            created=created,
            indexed=True,
            chunk_count=len(chunks),
        )
