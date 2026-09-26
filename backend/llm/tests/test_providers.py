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
from llm.schemas import (
    LLMMessage,
    LLMToolDefinition,
)


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

        if kwargs.get(
            "stream"
        ):
            return iter(
                [
                    SimpleNamespace(
                        id="evren-stream-1",
                        choices=[
                            SimpleNamespace(
                                delta=
                                    SimpleNamespace(
                                        content=
                                            "EVREN "
                                    )
                            )
                        ],
                        usage=None,
                    ),
                    SimpleNamespace(
                        id="evren-stream-1",
                        choices=[
                            SimpleNamespace(
                                delta=
                                    SimpleNamespace(
                                        content=
                                            "stream"
                                    )
                            )
                        ],
                        usage=None,
                    ),
                    SimpleNamespace(
                        id="evren-stream-1",
                        choices=[],
                        usage=
                            SimpleNamespace(
                                prompt_tokens=12,
                                completion_tokens=7,
                            ),
                    ),
                ]
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



def test_anthropic_provider_uses_claude_agent_sdk_for_tools(
    monkeypatch,
):
    class FakeAdapter:
        def __init__(
            self,
            *,
            api_key,
            model,
        ):
            assert api_key == "test-key"
            assert model == "test-claude"

        def run(
            self,
            messages,
            *,
            tools,
            tool_executor,
            system,
            max_steps,
        ):
            assert (
                messages[0].content
                == "Kaniti ara"
            )

            assert (
                tools[0].name
                == "search_evidence"
            )

            assert system == "test-system"
            assert max_steps == 3

            return SimpleNamespace(
                text="SDK sonucu",
                input_tokens=21,
                output_tokens=9,
                tool_calls=[
                    {
                        "id":
                            "claude-sdk-1",
                        "name":
                            "search_evidence",
                        "arguments": {
                            "claim":
                                "test",
                        },
                        "status":
                            "success",
                    }
                ],
                metadata={
                    "agent_sdk": True,
                    "session_id":
                        "test-session",
                },
            )

    monkeypatch.setattr(
        (
            "agent.claude_sdk_adapter."
            "ClaudeAgentSDKAdapter"
        ),
        FakeAdapter,
    )

    provider = AnthropicProvider(
        api_key="test-key",
        model="test-claude",
    )

    tool = LLMToolDefinition(
        name="search_evidence",
        description="Evidence ara",
        parameters={
            "type": "object",
            "properties": {
                "claim": {
                    "type": "string",
                },
            },
            "required": [
                "claim",
            ],
        },
    )

    response = (
        provider.generate_with_tools(
            [
                LLMMessage(
                    role="user",
                    content="Kaniti ara",
                )
            ],
            tools=[
                tool,
            ],
            tool_executor=(
                lambda name, arguments:
                    {
                        "name": name,
                        "arguments":
                            arguments,
                    }
            ),
            system="test-system",
            max_steps=3,
        )
    )

    assert response.text == "SDK sonucu"
    assert response.input_tokens == 21
    assert response.output_tokens == 9

    assert (
        response.tool_calls[0]["name"]
        == "search_evidence"
    )

    assert (
        response.metadata["agent_sdk"]
        is True
    )

    assert (
        response.metadata["transport"]
        == "claude-agent-sdk"
    )


def test_anthropic_sdk_stream_maps_events(
    monkeypatch,
):
    class FakeAdapter:
        def __init__(
            self,
            *,
            api_key,
            model,
        ):
            assert api_key == "test-key"
            assert model == "test-claude"

        def stream(
            self,
            messages,
            *,
            tools,
            tool_executor,
            system,
            max_steps,
        ):
            yield SimpleNamespace(
                type="tool_start",
                delta="",
                tool_call={
                    "id":
                        "claude-sdk-1",
                    "name":
                        "search_evidence",
                },
                result=None,
            )

            yield SimpleNamespace(
                type="tool_end",
                delta="",
                tool_call={
                    "id":
                        "claude-sdk-1",
                    "name":
                        "search_evidence",
                    "status":
                        "success",
                },
                result=None,
            )

            yield SimpleNamespace(
                type="delta",
                delta="Final ",
                tool_call=None,
                result=None,
            )

            yield SimpleNamespace(
                type="delta",
                delta="SDK cevabi",
                tool_call=None,
                result=None,
            )

            yield SimpleNamespace(
                type="done",
                delta="",
                tool_call=None,
                result=
                    SimpleNamespace(
                        text=
                            "Final SDK cevabi",
                        input_tokens=10,
                        output_tokens=5,
                        tool_calls=[
                            {
                                "id":
                                    "claude-sdk-1",
                                "name":
                                    "search_evidence",
                                "status":
                                    "success",
                            }
                        ],
                        metadata={
                            "agent_sdk":
                                True,
                        },
                    ),
            )

    monkeypatch.setattr(
        (
            "agent.claude_sdk_adapter."
            "ClaudeAgentSDKAdapter"
        ),
        FakeAdapter,
    )

    provider = AnthropicProvider(
        api_key="test-key",
        model="test-claude",
    )

    tool = LLMToolDefinition(
        name="search_evidence",
        description="Evidence ara",
        parameters={
            "type": "object",
            "properties": {},
        },
    )

    events = list(
        provider.stream_with_tools(
            [
                LLMMessage(
                    role="user",
                    content="Test",
                )
            ],
            tools=[
                tool,
            ],
            tool_executor=(
                lambda name, arguments:
                    {}
            ),
        )
    )

    assert [
        event.type
        for event in events
    ] == [
        "tool_start",
        "tool_end",
        "delta",
        "delta",
        "done",
    ]

    assert (
        events[0]
        .tool_call["name"]
        == "search_evidence"
    )

    assert (
        events[1]
        .tool_call["status"]
        == "success"
    )

    assert (
        events[2].delta
        == "Final "
    )

    assert (
        events[3].delta
        == "SDK cevabi"
    )

    response = (
        events[4].response
    )

    assert response is not None

    assert (
        response.text
        == "Final SDK cevabi"
    )

    assert (
        response.metadata[
            "transport"
        ]
        == "claude-agent-sdk"
    )

    assert (
        response.metadata[
            "native_stream"
        ]
        is True
    )


def test_evren_provider_native_streams_deltas():
    provider = EvrenProvider(
        api_key="test",
        base_url="https://example.test/v1",
        model="test-evren",
        client=FakeEvrenClient(),
    )

    events = list(
        provider.stream_with_tools(
            [
                LLMMessage(
                    role="user",
                    content="Streaming testi",
                )
            ],
            tools=[],
            tool_executor=(
                lambda name, arguments:
                    None
            ),
        )
    )

    assert [
        event.type
        for event in events
    ] == [
        "delta",
        "delta",
        "done",
    ]

    assert (
        events[0].delta
        == "EVREN "
    )

    assert (
        events[1].delta
        == "stream"
    )

    response = (
        events[-1].response
    )

    assert response is not None

    assert (
        response.text
        == "EVREN stream"
    )

    assert (
        response.provider
        == "evren"
    )

    assert (
        response.input_tokens
        == 12
    )

    assert (
        response.output_tokens
        == 7
    )

    assert (
        response.metadata[
            "transport"
        ]
        == "evren-native-stream"
    )
