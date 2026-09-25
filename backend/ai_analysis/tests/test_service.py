from llm.schemas import (
    LLMResponse,
)

from ai_analysis.evidence_retriever import (
    EvidenceRetriever,
)
from ai_analysis.schemas import (
    Claim,
    EvidenceItem,
)
from ai_analysis.service import (
    run_ai_evidence_analysis,
)


class UnconfiguredProvider:
    name = "test"
    model = "test-model"
    configured = False


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
                  "text": "Test claim",
                  "check_worthy": true,
                  "rationale": "Dogrulanabilir"
                }
              ]
            }
            """,
            """
            {
              "stance": "support",
              "evidence_strength": "medium",
              "reasoning": "Kanit claim'i destekliyor.",
              "supporting_evidence_ids": ["evidence-1"],
              "contradicting_evidence_ids": [],
              "neutral_evidence_ids": []
            }
            """,
            """
            {
              "signals": []
            }
            """,
        ]

    def generate(
        self,
        messages,
        *,
        system=None,
    ):
        return LLMResponse(
            text=self.responses.pop(0),
            provider=self.name,
            model=self.model,
        )


class FakeRetriever(
    EvidenceRetriever
):
    mode = "test"

    def retrieve(
        self,
        claim: Claim,
        *,
        limit: int = 5,
    ):
        return [
            EvidenceItem(
                id="evidence-1",
                title="Evidence",
                url=(
                    "https://example.test/"
                    "evidence"
                ),
                source="Example",
                summary=(
                    "Claim'i destekleyen "
                    "kaynak."
                ),
                evidence_type="fact_check",
            )
        ]


def test_service_returns_unavailable_without_provider_configuration():
    result = run_ai_evidence_analysis(
        "Test claim",
        provider=(
            UnconfiguredProvider()
        ),
    )

    assert (
        result["status"]
        == "unavailable"
    )

    assert (
        result["reason"]
        == "llm_provider_not_configured"
    )


def test_service_returns_grounded_report():
    result = run_ai_evidence_analysis(
        "Test claim",
        provider=FakeProvider(),
        retriever=FakeRetriever(),
    )

    assert (
        result["status"]
        == "completed"
    )

    assert (
        result["report"][
            "overall_evidence_status"
        ]
        == "supported"
    )

    assert (
        result["report"][
            "retrieval_mode"
        ]
        == "test"
    )
