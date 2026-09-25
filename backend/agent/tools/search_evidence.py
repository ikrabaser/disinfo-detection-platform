from __future__ import annotations

from agent.tools.permissions import (
    tool_permission,
)
from ai_analysis.rag_retriever import (
    RAGEvidenceRetriever,
)
from ai_analysis.schemas import Claim


@tool_permission(
    roles={
        "admin",
        "analyst",
    }
)
def search_evidence(
    claim: str,
    limit: int = 5,
) -> dict:
    """
    Bir iddia icin canli fact-check/haber kaynaklarini
    tarar ve pgvector RAG ile en alakali evidence
    parcalarini getirir.

    Semantic similarity bir dogruluk veya
    guvenilirlik skoru degildir.
    """

    normalized = (
        " ".join(
            str(claim).split()
        ).strip()
    )

    if not normalized:
        raise ValueError(
            "claim bos olamaz."
        )

    try:
        normalized_limit = int(
            limit
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            "limit sayisal olmali."
        ) from exc

    normalized_limit = max(
        1,
        min(
            normalized_limit,
            8,
        ),
    )

    retriever = (
        RAGEvidenceRetriever()
    )

    evidence = retriever.retrieve(
        Claim(
            id="assistant-claim",
            text=normalized,
            check_worthy=True,
            rationale=(
                "VERITAS Assistant "
                "evidence search"
            ),
        ),
        limit=normalized_limit,
    )

    return {
        "claim": normalized,
        "retrieval_mode":
            retriever.mode,
        "count":
            len(evidence),
        "evidence": [
            item.to_dict()
            for item in evidence
        ],
        "limitations": [
            (
                "Semantic similarity "
                "dogruluk veya kaynak "
                "guvenilirligi anlamina gelmez."
            ),
            (
                "Yanit yalnizca bulunan "
                "evidence kaynaklariyla "
                "sinirlidir."
            ),
        ],
    }
