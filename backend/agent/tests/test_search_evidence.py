from __future__ import annotations

from ai_analysis.schemas import (
    EvidenceItem,
)
from agent.tools import (
    search_evidence,
)
import importlib

search_evidence_module = (
    importlib.import_module(
        "agent.tools.search_evidence"
    )
)


class FakeRetriever:
    mode = (
        "test-fact-check"
        "+pgvector-rag"
    )

    def retrieve(
        self,
        claim,
        *,
        limit,
    ):
        assert (
            claim.text
            == "Ornek iddia"
        )

        assert limit == 3

        return [
            EvidenceItem(
                id="rag-1",
                title="Test evidence",
                url=(
                    "https://example.com/evidence"
                ),
                source="Example",
                content=(
                    "Iddia ile ilgili "
                    "kanit metni."
                ),
                content_status=
                    "fetched",
                evidence_type=
                    "rag_chunk",
                retrieval_source=
                    "pgvector",
                metadata={
                    "similarity": 0.81,
                },
            )
        ]


def test_search_evidence_returns_grounded_items(
    monkeypatch,
):
    monkeypatch.setattr(
        search_evidence_module,
        "RAGEvidenceRetriever",
        FakeRetriever,
    )

    result = search_evidence(
        claim="  Ornek   iddia  ",
        limit=3,
    )

    assert result["count"] == 1

    assert (
        result["evidence"][0][
            "evidence_type"
        ]
        == "rag_chunk"
    )

    assert (
        result["evidence"][0][
            "metadata"
        ][
            "similarity"
        ]
        == 0.81
    )
