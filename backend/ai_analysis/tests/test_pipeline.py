from llm.schemas import LLMResponse

from ai_analysis.evidence_retriever import (
    EvidenceRetriever,
)
from ai_analysis.json_utils import (
    parse_json_object,
)
from ai_analysis.orchestrator import (
    DisinformationAnalysisOrchestrator,
)
from ai_analysis.schemas import (
    Claim,
    EvidenceItem,
)


class FakeProvider:
    name = "fake"
    model = "fake-model"
    configured = True

    def __init__(self):
        self.responses = [
            """
            {
              "claims": [
                {
                  "text": "Firma X urununu toplatti.",
                  "check_worthy": true,
                  "rationale": "Dogrulanabilir iddia"
                }
              ]
            }
            """,
            """
            {
              "stance": "contradict",
              "evidence_strength": "high",
              "reasoning": "Resmi kaynak iddiayi reddediyor.",
              "supporting_evidence_ids": [],
              "contradicting_evidence_ids": ["evidence-1"],
              "neutral_evidence_ids": []
            }
            """,
            """
            {
              "signals": [
                {
                  "signal_type": "sensational_language",
                  "severity": "medium",
                  "excerpt": "SOK!",
                  "explanation": "Sansasyonel dil kullaniliyor."
                }
              ]
            }
            """,
        ]

    def generate(
        self,
        messages,
        *,
        system=None,
    ):
        assert system is not None

        return LLMResponse(
            text=self.responses.pop(0),
            provider=self.name,
            model=self.model,
        )


class FakeRetriever(
    EvidenceRetriever
):
    mode = "test-retrieval"

    def retrieve(
        self,
        claim: Claim,
        *,
        limit: int = 5,
    ):
        assert (
            claim.text
            == "Firma X urununu toplatti."
        )

        return [
            EvidenceItem(
                id="evidence-1",
                title="Resmi aciklama",
                url=(
                    "https://example.test/"
                    "official"
                ),
                source="Official",
                summary=(
                    "Firma toplatma "
                    "iddiasini reddetti."
                ),
            )
        ]


def test_parse_json_object_handles_fence():
    payload = parse_json_object(
        """```json
        {"value": 1}
        ```"""
    )

    assert payload["value"] == 1


def test_pipeline_builds_evidence_grounded_report():
    orchestrator = (
        DisinformationAnalysisOrchestrator(
            provider=FakeProvider(),
            retriever=FakeRetriever(),
        )
    )

    result = orchestrator.run(
        "SOK! Firma X urununu toplatti."
    )

    assert (
        result.overall_evidence_status
        == "contradicted"
    )

    assert len(result.claims) == 1
    assert len(result.assessments) == 1

    assert (
        result.assessments[0].stance
        == "contradict"
    )

    assert (
        result.manipulation_signals[
            0
        ].signal_type
        == "sensational_language"
    )

    assert (
        result.retrieval_mode
        == "test-retrieval"
    )


def test_overall_status_mixed():
    from ai_analysis.schemas import (
        ClaimAssessment,
    )

    assessments = [
        ClaimAssessment(
            claim_id="1",
            stance="support",
            evidence_strength="medium",
            reasoning="support",
        ),
        ClaimAssessment(
            claim_id="2",
            stance="contradict",
            evidence_strength="medium",
            reasoning="contradict",
        ),
    ]

    status = (
        DisinformationAnalysisOrchestrator
        ._overall_status(
            assessments
        )
    )

    assert status == "mixed"


def test_overall_status_insufficient():
    assert (
        DisinformationAnalysisOrchestrator
        ._overall_status([])
        == "insufficient"
    )
