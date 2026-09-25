from types import SimpleNamespace

import pytest

from llm.providers.anthropic_provider import (
    AnthropicProvider,
)
from llm.providers.evren_provider import (
    EvrenProvider,
)
from llm.providers.openai_provider import (
    OpenAIProvider,
)
from llm.registry import (
    get_llm_provider,
)
from llm.schemas import LLMMessage


class FakeOpenAIResponses:
    def create(self, **kwargs):
        assert (
            kwargs["model"]
            == "test-openai"
        )

        return SimpleNamespace(
            id="resp-1",
            output_text="OpenAI test",
            usage=SimpleNamespace(
                input_tokens=10,
                output_tokens=5,
            ),
        )


class FakeOpenAIClient:
    def __init__(self):
        self.responses = (
            FakeOpenAIResponses()
        )


class FakeAnthropicMessages:
    def create(self, **kwargs):
        assert (
            kwargs["model"]
            == "test-claude"
        )

        return SimpleNamespace(
            id="msg-1",
            content=[
                SimpleNamespace(
                    type="text",
                    text="Claude test",
                )
            ],
            usage=SimpleNamespace(
                input_tokens=11,
                output_tokens=6,
            ),
        )


class FakeAnthropicClient:
    def __init__(self):
        self.messages = (
            FakeAnthropicMessages()
        )


class FakeEvrenCompletions:
    def create(self, **kwargs):
        assert (
            kwargs["model"]
            == "test-evren"
        )

        return SimpleNamespace(
            id="evren-1",
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="EVREN test"
                    )
                )
            ],
            usage=SimpleNamespace(
                prompt_tokens=12,
                completion_tokens=7,
            ),
        )


class FakeEvrenClient:
    def __init__(self):
        self.chat = SimpleNamespace(
            completions=(
                FakeEvrenCompletions()
            )
        )


def test_openai_provider_maps_response():
    provider = OpenAIProvider(
        api_key="test",
        model="test-openai",
        client=FakeOpenAIClient(),
    )

    response = provider.generate(
        [
            LLMMessage(
                role="user",
                content="Merhaba",
            )
        ]
    )

    assert response.text == "OpenAI test"
    assert response.provider == "openai"
    assert response.input_tokens == 10


def test_anthropic_provider_maps_response(
    settings,
):
    settings.ANTHROPIC_MAX_TOKENS = 512

    provider = AnthropicProvider(
        api_key="test",
        model="test-claude",
        client=FakeAnthropicClient(),
    )

    response = provider.generate(
        [
            LLMMessage(
                role="user",
                content="Merhaba",
            )
        ]
    )

    assert response.text == "Claude test"
    assert (
        response.provider
        == "anthropic"
    )
    assert response.output_tokens == 6


def test_evren_provider_maps_response():
    provider = EvrenProvider(
        api_key="test",
        base_url="https://example.test/v1",
        model="test-evren",
        client=FakeEvrenClient(),
    )

    response = provider.generate(
        [
            LLMMessage(
                role="user",
                content="Merhaba",
            )
        ]
    )

    assert response.text == "EVREN test"
    assert response.provider == "evren"
    assert response.output_tokens == 7


def test_registry_uses_default_provider(
    settings,
):
    settings.DEFAULT_LLM_PROVIDER = (
        "openai"
    )

    provider = get_llm_provider()

    assert isinstance(
        provider,
        OpenAIProvider,
    )


def test_registry_accepts_claude_alias():
    provider = get_llm_provider(
        "claude"
    )

    assert isinstance(
        provider,
        AnthropicProvider,
    )


def test_registry_rejects_unknown_provider():
    with pytest.raises(
        ValueError,
        match="Bilinmeyen LLM provider",
    ):
        get_llm_provider(
            "bilinmeyen"
        )
