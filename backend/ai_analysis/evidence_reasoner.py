from __future__ import annotations

import json

from llm import (
    LLMMessage,
    LLMProvider,
)

from ai_analysis.json_utils import (
    parse_json_object,
)
from ai_analysis.schemas import (
    Claim,
    ClaimAssessment,
    EvidenceItem,
)


EVIDENCE_REASONING_SYSTEM = """
Sen VERITAS Evidence Reasoning bileşenisin.

Sana bir claim ve yalnızca o claim için
geri getirilen evidence kayıtları verilecek.

Sadece verilen evidence üzerinden karar ver.

Stance değerlerinden yalnızca birini kullan:
- support
- contradict
- neutral
- insufficient

Kurallar:
- dışarıdan bilgi ekleme,
- kaynakta olmayan çıkarım üretme,
- confidence yüzdesi üretme,
- model tahminini gerçeklik kanıtı sayma,
- kanıt yetersizse insufficient kullan.

Yalnızca şu JSON formatını döndür:

{
  "stance": "support",
  "evidence_strength": "low",
  "reasoning": "...",
  "supporting_evidence_ids": [],
  "contradicting_evidence_ids": [],
  "neutral_evidence_ids": []
}
""".strip()


class EvidenceReasoner:
    def __init__(
        self,
        provider: LLMProvider,
    ):
        self.provider = provider

    def assess(
        self,
        claim: Claim,
        evidence: list[EvidenceItem],
    ) -> ClaimAssessment:
        if not evidence:
            return ClaimAssessment(
                claim_id=claim.id,
                stance="insufficient",
                evidence_strength="low",
                reasoning=(
                    "Bu iddia icin "
                    "kullanilabilir kanit "
                    "bulunamadi."
                ),
            )

        evidence_payload = [
            item.to_dict()
            for item in evidence
        ]

        user_content = json.dumps(
            {
                "claim": {
                    "id": claim.id,
                    "text": claim.text,
                },
                "evidence":
                    evidence_payload,
            },
            ensure_ascii=False,
        )

        response = self.provider.generate(
            [
                LLMMessage(
                    role="user",
                    content=user_content,
                )
            ],
            system=(
                EVIDENCE_REASONING_SYSTEM
            ),
        )

        payload = parse_json_object(
            response.text
        )

        stance = str(
            payload.get(
                "stance",
                "insufficient",
            )
        ).lower()

        if stance not in {
            "support",
            "contradict",
            "neutral",
            "insufficient",
        }:
            stance = "insufficient"

        strength = str(
            payload.get(
                "evidence_strength",
                "low",
            )
        ).lower()

        if strength not in {
            "low",
            "medium",
            "high",
        }:
            strength = "low"

        return ClaimAssessment(
            claim_id=claim.id,
            stance=stance,
            evidence_strength=strength,
            reasoning=str(
                payload.get(
                    "reasoning",
                    "",
                )
            ).strip(),
            supporting_evidence_ids=[
                str(item)
                for item in payload.get(
                    "supporting_evidence_ids",
                    [],
                )
            ],
            contradicting_evidence_ids=[
                str(item)
                for item in payload.get(
                    "contradicting_evidence_ids",
                    [],
                )
            ],
            neutral_evidence_ids=[
                str(item)
                for item in payload.get(
                    "neutral_evidence_ids",
                    [],
                )
            ],
        )
