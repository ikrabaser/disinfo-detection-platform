from __future__ import annotations

from abc import (
    ABC,
    abstractmethod,
)
from typing import Any

from django.conf import settings


class EmbeddingError(
    RuntimeError
):
    pass


class EmbeddingConfigurationError(
    EmbeddingError
):
    pass


class EmbeddingProvider(ABC):
    model: str
    dimensions: int

    @abstractmethod
    def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        pass


class OpenAIEmbeddingProvider(
    EmbeddingProvider
):
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        dimensions: int | None = None,
        client: Any | None = None,
    ):
        self.api_key = (
            settings.OPENAI_API_KEY
            if api_key is None
            else api_key
        )

        self.model = (
            settings.OPENAI_EMBEDDING_MODEL
            if model is None
            else model
        )

        self.dimensions = (
            settings
            .OPENAI_EMBEDDING_DIMENSIONS
            if dimensions is None
            else dimensions
        )

        self._client = client

    @property
    def configured(self) -> bool:
        return bool(
            self.api_key
            or self._client is not None
        )

    def _get_client(self):
        if self._client is not None:
            return self._client

        if not self.api_key:
            raise (
                EmbeddingConfigurationError(
                    "OPENAI_API_KEY "
                    "tanimli degil."
                )
            )

        from openai import OpenAI

        self._client = OpenAI(
            api_key=self.api_key
        )

        return self._client

    def embed(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        if not texts:
            return []

        client = self._get_client()

        response = (
            client.embeddings.create(
                model=self.model,
                input=texts,
            )
        )

        ordered = sorted(
            response.data,
            key=lambda item: (
                getattr(
                    item,
                    "index",
                    0,
                )
            ),
        )

        vectors = [
            list(item.embedding)
            for item in ordered
        ]

        if len(vectors) != len(
            texts
        ):
            raise EmbeddingError(
                "Embedding sayisi input "
                "sayisiyla eslesmiyor."
            )

        for vector in vectors:
            if len(vector) != (
                self.dimensions
            ):
                raise EmbeddingError(
                    "Embedding dimension "
                    f"beklenen "
                    f"{self.dimensions}, "
                    f"gelen {len(vector)}."
                )

        return vectors
