from __future__ import annotations

from dataclasses import dataclass

import tiktoken
from django.conf import settings


@dataclass(slots=True)
class TextChunk:
    index: int
    text: str
    token_count: int
    start_token: int
    end_token: int


class TokenChunker:
    def __init__(
        self,
        *,
        max_tokens: int | None = None,
        overlap: int | None = None,
    ):
        self.max_tokens = (
            settings.RAG_CHUNK_TOKENS
            if max_tokens is None
            else max_tokens
        )

        self.overlap = (
            settings.RAG_CHUNK_OVERLAP
            if overlap is None
            else overlap
        )

        if self.max_tokens <= 0:
            raise ValueError(
                "max_tokens pozitif olmali."
            )

        if (
            self.overlap < 0
            or self.overlap
            >= self.max_tokens
        ):
            raise ValueError(
                "overlap, max_tokens'tan "
                "kucuk ve negatif olmayan "
                "bir deger olmali."
            )

        self.encoding = (
            tiktoken.get_encoding(
                "cl100k_base"
            )
        )

    def chunk(
        self,
        text: str,
    ) -> list[TextChunk]:
        normalized = text.strip()

        if not normalized:
            return []

        tokens = self.encoding.encode(
            normalized
        )

        chunks: list[
            TextChunk
        ] = []

        start = 0
        index = 0

        while start < len(tokens):
            end = min(
                start + self.max_tokens,
                len(tokens),
            )

            chunk_tokens = tokens[
                start:end
            ]

            chunk_text = (
                self.encoding.decode(
                    chunk_tokens
                ).strip()
            )

            if chunk_text:
                chunks.append(
                    TextChunk(
                        index=index,
                        text=chunk_text,
                        token_count=len(
                            chunk_tokens
                        ),
                        start_token=start,
                        end_token=end,
                    )
                )

                index += 1

            if end >= len(tokens):
                break

            start = (
                end - self.overlap
            )

        return chunks
