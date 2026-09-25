from __future__ import annotations

from django.db import models
from pgvector.django import VectorField


class EvidenceDocument(models.Model):
    url = models.URLField(
        max_length=2048,
        unique=True,
    )

    title = models.CharField(
        max_length=500,
        blank=True,
    )

    source = models.CharField(
        max_length=255,
        blank=True,
    )

    language = models.CharField(
        max_length=32,
        blank=True,
    )

    retrieval_source = models.CharField(
        max_length=64,
        blank=True,
    )

    content = models.TextField()

    content_hash = models.CharField(
        max_length=64,
        db_index=True,
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = [
            "-updated_at"
        ]

    def __str__(self) -> str:
        return (
            self.title
            or self.url
        )


class EvidenceChunk(models.Model):
    document = models.ForeignKey(
        EvidenceDocument,
        on_delete=models.CASCADE,
        related_name="chunks",
    )

    chunk_index = models.PositiveIntegerField()

    text = models.TextField()

    token_count = models.PositiveIntegerField()

    embedding_model = models.CharField(
        max_length=100,
    )

    embedding = VectorField(
        dimensions=1536,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = [
            "document_id",
            "chunk_index",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "document",
                    "chunk_index",
                ],
                name=(
                    "unique_evidence_"
                    "document_chunk"
                ),
            )
        ]

    def __str__(self) -> str:
        return (
            f"EvidenceChunk "
            f"{self.document_id}:"
            f"{self.chunk_index}"
        )
