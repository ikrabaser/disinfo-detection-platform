from __future__ import annotations

from dataclasses import dataclass

from django.conf import settings

from analyses.models import (
    AnalysisMode,
)


@dataclass(
    frozen=True,
    slots=True,
)
class AnalysisProfile:
    mode: str
    provider: str
    model: str
    evidence_limit: int


def get_analysis_profile(
    mode: str,
) -> AnalysisProfile:
    if mode == AnalysisMode.DEEP:
        return AnalysisProfile(
            mode=AnalysisMode.DEEP,
            provider="anthropic",
            model=
                settings.ANTHROPIC_CHAT_MODEL,
            evidence_limit=10,
        )

    return AnalysisProfile(
        mode=AnalysisMode.FAST,
        provider="openai",
        model=
            settings.OPENAI_CHAT_MODEL,
        evidence_limit=3,
    )
