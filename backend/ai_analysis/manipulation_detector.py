from __future__ import annotations

from llm import (
    LLMMessage,
    LLMProvider,
)

from ai_analysis.json_utils import (
    parse_json_object,
)
from ai_analysis.schemas import (
    ManipulationSignal,
)


MANIPULATION_SYSTEM = """
Sen VERITAS Manipulation Analysis
bileşenisin.

Metindeki dilsel ve retorik manipülasyon
sinyallerini analiz et.

Ornek sinyaller:
- sensational_language
- fear_appeal
- missing_source_attribution
- unverifiable_authority_claim
- conspiracy_framing
- false_urgency
- context_omission
- excessive_certainty

Bir sinyalin bulunmasi haberin sahte oldugu
anlamina gelmez.

Metinde olmayan sinyal uydurma.

Yalnızca şu JSON formatını döndür:

{
  "signals": [
    {
      "signal_type": "...",
      "severity": "low",
      "excerpt": "...",
      "explanation": "..."
    }
  ]
}
""".strip()


class ManipulationDetector:
    def __init__(
        self,
        provider: LLMProvider,
    ):
        self.provider = provider

    def analyze(
        self,
        text: str,
    ) -> list[ManipulationSignal]:
        response = self.provider.generate(
            [
                LLMMessage(
                    role="user",
                    content=text,
                )
            ],
            system=MANIPULATION_SYSTEM,
        )

        payload = parse_json_object(
            response.text
        )

        raw_signals = payload.get(
            "signals",
            [],
        )

        signals: list[
            ManipulationSignal
        ] = []

        if not isinstance(
            raw_signals,
            list,
        ):
            return signals

        for item in raw_signals:
            if not isinstance(
                item,
                dict,
            ):
                continue

            severity = str(
                item.get(
                    "severity",
                    "low",
                )
            ).lower()

            if severity not in {
                "low",
                "medium",
                "high",
            }:
                severity = "low"

            signals.append(
                ManipulationSignal(
                    signal_type=str(
                        item.get(
                            "signal_type",
                            "unknown",
                        )
                    ),
                    severity=severity,
                    excerpt=str(
                        item.get(
                            "excerpt",
                            "",
                        )
                    ),
                    explanation=str(
                        item.get(
                            "explanation",
                            "",
                        )
                    ),
                )
            )

        return signals
