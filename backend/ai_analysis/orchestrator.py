from __future__ import annotations

from llm import LLMProvider

from ai_analysis.claim_extractor import (
    ClaimExtractor,
)
from ai_analysis.evidence_reasoner import (
    EvidenceReasoner,
)
from ai_analysis.evidence_retriever import (
    EvidenceRetriever,
)
from ai_analysis.rag_retriever import (
    RAGEvidenceRetriever,
)
from ai_analysis.manipulation_detector import (
    ManipulationDetector,
)
from ai_analysis.schemas import (
    ClaimAssessment,
    DisinformationReport,
)


class DisinformationAnalysisOrchestrator:
    def __init__(
        self,
        provider: LLMProvider,
        retriever:
            EvidenceRetriever | None = None,
    ):
        self.provider = provider

        self.retriever = (
            retriever
            or RAGEvidenceRetriever()
        )

        self.claim_extractor = (
            ClaimExtractor(provider)
        )

        self.evidence_reasoner = (
            EvidenceReasoner(provider)
        )

        self.manipulation_detector = (
            ManipulationDetector(provider)
        )

    @staticmethod
    def _overall_status(
        assessments:
            list[ClaimAssessment],
    ) -> str:
        if not assessments:
            return "insufficient"

        stances = {
            item.stance
            for item in assessments
        }

        has_support = (
            "support" in stances
        )

        has_contradict = (
            "contradict" in stances
        )

        if (
            has_support
            and has_contradict
        ):
            return "mixed"

        if has_contradict:
            return "contradicted"

        if (
            has_support
            and stances.issubset(
                {
                    "support",
                    "neutral",
                }
            )
        ):
            return "supported"

        return "insufficient"

    def run(
        self,
        text: str,
    ) -> DisinformationReport:
        claims = (
            self.claim_extractor.extract(
                text
            )
        )

        evidence_by_claim = {}
        assessments = []

        for claim in claims:
            if not claim.check_worthy:
                continue

            evidence = (
                self.retriever.retrieve(
                    claim,
                    limit=5,
                )
            )

            evidence_by_claim[
                claim.id
            ] = evidence

            assessment = (
                self.evidence_reasoner
                .assess(
                    claim,
                    evidence,
                )
            )

            assessments.append(
                assessment
            )

        manipulation_signals = (
            self.manipulation_detector
            .analyze(text)
        )

        overall_status = (
            self._overall_status(
                assessments
            )
        )

        return DisinformationReport(
            provider=self.provider.name,
            model=self.provider.model,
            overall_evidence_status=
                overall_status,
            claims=claims,
            evidence=evidence_by_claim,
            assessments=assessments,
            manipulation_signals=
                manipulation_signals,
            retrieval_mode=
                self.retriever.mode,
            limitations=[
                (
                    "Sonuc yalnizca geri "
                    "getirilen kanitlara "
                    "dayanir."
                ),
                (
                    "LLM gercekligin hakemi "
                    "olarak kullanilmaz."
                ),
                (
                    "NLP, GNN ve bot model "
                    "skorlari kanit yerine "
                    "gecmez."
                ),
            ],
        )
