from __future__ import annotations

from llm import (
    LLMProvider,
    get_llm_provider,
)

from ai_analysis.evidence_retriever import (
    EvidenceRetriever,
)
from ai_analysis.orchestrator import (
    DisinformationAnalysisOrchestrator,
)


def run_ai_evidence_analysis(
    text: str,
    *,
    provider: LLMProvider | None = None,
    retriever:
        EvidenceRetriever | None = None,
    evidence_limit: int = 5,
) -> dict:
    normalized = text.strip()

    if not normalized:
        raise ValueError(
            "AI evidence analysis metni bos olamaz."
        )

    selected_provider = (
        provider
        if provider is not None
        else get_llm_provider()
    )

    if not selected_provider.configured:
        return {
            "status": "unavailable",
            "provider":
                selected_provider.name,
            "model":
                selected_provider.model,
            "reason":
                "llm_provider_not_configured",
            "report": None,
        }

    orchestrator = (
        DisinformationAnalysisOrchestrator(
            provider=selected_provider,
            retriever=retriever,
        )
    )

    report = orchestrator.run(
        normalized,
        evidence_limit=
            evidence_limit,
    )

    return {
        "status": "completed",
        "provider":
            selected_provider.name,
        "model":
            selected_provider.model,
        "report": report.to_dict(),
    }
