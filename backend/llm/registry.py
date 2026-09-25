from __future__ import annotations

from django.conf import settings

from llm.base import LLMProvider
from llm.providers.anthropic_provider import (
    AnthropicProvider,
)
from llm.providers.evren_provider import (
    EvrenProvider,
)
from llm.providers.openai_provider import (
    OpenAIProvider,
)


def get_llm_provider(
    provider_name: str | None = None,
) -> LLMProvider:
    name = (
        provider_name
        or settings.DEFAULT_LLM_PROVIDER
    ).strip().lower()

    if name == "openai":
        return OpenAIProvider()

    if name in {
        "anthropic",
        "claude",
    }:
        return AnthropicProvider()

    if name == "evren":
        return EvrenProvider()

    raise ValueError(
        f"Bilinmeyen LLM provider: {name}"
    )


def get_provider_catalog():
    providers = [
        OpenAIProvider(),
        AnthropicProvider(),
        EvrenProvider(),
    ]

    return [
        {
            "name": provider.name,
            "model": provider.model,
            "configured":
                provider.configured,
        }
        for provider in providers
    ]
