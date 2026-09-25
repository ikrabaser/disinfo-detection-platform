from __future__ import annotations

from llm import (
    LLMConfigurationError,
    LLMMessage,
    LLMProvider,
)

from ai_analysis.json_utils import (
    parse_json_object,
)
from ai_analysis.schemas import Claim


CLAIM_EXTRACTION_SYSTEM = """
Sen VERITAS Claim Extraction bileşenisin.

Girdideki metinden yalnızca dış kaynaklarla
doğrulanabilecek somut iddiaları çıkar.

Kurallar:
- yorumları ve kişisel görüşleri claim yapma,
- aynı claim'i tekrar etme,
- metinde olmayan bilgi ekleme,
- siyasi, ekonomik veya sosyal konularda
  taraf tutma,
- doğruluğa ilişkin karar verme,
- yalnızca kontrol edilmesi anlamlı olan
  iddiaları check_worthy=true yap.

Yalnızca aşağıdaki JSON formatını döndür:

{
  "claims": [
    {
      "text": "...",
      "check_worthy": true,
      "rationale": "..."
    }
  ]
}
""".strip()


class ClaimExtractor:
    def __init__(
        self,
        provider: LLMProvider,
    ):
        self.provider = provider

    def extract(
        self,
        text: str,
    ) -> list[Claim]:
        normalized = text.strip()

        if not normalized:
            raise ValueError(
                "Analiz metni bos olamaz."
            )

        if not self.provider.configured:
            raise LLMConfigurationError(
                "Claim extraction icin "
                "LLM provider configure "
                "edilmemis."
            )

        response = self.provider.generate(
            [
                LLMMessage(
                    role="user",
                    content=normalized,
                )
            ],
            system=(
                CLAIM_EXTRACTION_SYSTEM
            ),
        )

        payload = parse_json_object(
            response.text
        )

        raw_claims = payload.get(
            "claims",
            [],
        )

        if not isinstance(
            raw_claims,
            list,
        ):
            raise ValueError(
                "'claims' list olmali."
            )

        claims: list[Claim] = []

        for index, item in enumerate(
            raw_claims[:8],
            start=1,
        ):
            if not isinstance(
                item,
                dict,
            ):
                continue

            claim_text = str(
                item.get(
                    "text",
                    "",
                )
            ).strip()

            if not claim_text:
                continue

            claims.append(
                Claim(
                    id=f"claim-{index}",
                    text=claim_text,
                    check_worthy=bool(
                        item.get(
                            "check_worthy",
                            True,
                        )
                    ),
                    rationale=str(
                        item.get(
                            "rationale",
                            "",
                        )
                    ).strip(),
                )
            )

        return claims
