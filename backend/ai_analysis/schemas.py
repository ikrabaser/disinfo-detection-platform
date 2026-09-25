from __future__ import annotations

from dataclasses import (
    asdict,
    dataclass,
    field,
)
from typing import Literal


EvidenceStance = Literal[
    "support",
    "contradict",
    "neutral",
    "insufficient",
]

EvidenceStrength = Literal[
    "low",
    "medium",
    "high",
]

OverallEvidenceStatus = Literal[
    "supported",
    "contradicted",
    "mixed",
    "insufficient",
]


@dataclass(slots=True)
class Claim:
    id: str
    text: str
    check_worthy: bool = True
    rationale: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class EvidenceItem:
    id: str
    title: str
    url: str
    source: str
    published_at: str | None = None
    summary: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class ClaimAssessment:
    claim_id: str
    stance: EvidenceStance
    evidence_strength: EvidenceStrength
    reasoning: str

    supporting_evidence_ids: list[str] = field(
        default_factory=list
    )

    contradicting_evidence_ids: list[str] = field(
        default_factory=list
    )

    neutral_evidence_ids: list[str] = field(
        default_factory=list
    )

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class ManipulationSignal:
    signal_type: str
    severity: EvidenceStrength
    excerpt: str
    explanation: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class DisinformationReport:
    provider: str
    model: str
    overall_evidence_status: OverallEvidenceStatus
    claims: list[Claim]

    evidence: dict[
        str,
        list[EvidenceItem],
    ]

    assessments: list[ClaimAssessment]

    manipulation_signals: list[
        ManipulationSignal
    ]

    retrieval_mode: str

    limitations: list[str] = field(
        default_factory=list
    )

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "overall_evidence_status":
                self.overall_evidence_status,
            "claims": [
                claim.to_dict()
                for claim in self.claims
            ],
            "evidence": {
                claim_id: [
                    item.to_dict()
                    for item in items
                ]
                for claim_id, items
                in self.evidence.items()
            },
            "assessments": [
                item.to_dict()
                for item
                in self.assessments
            ],
            "manipulation_signals": [
                item.to_dict()
                for item
                in self.manipulation_signals
            ],
            "retrieval_mode":
                self.retrieval_mode,
            "limitations":
                self.limitations,
        }
