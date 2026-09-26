from __future__ import annotations

from types import SimpleNamespace

import pytest

from accounts.models import (
    Role,
    User,
)
from agent.client import AgentRunner
from agent.tool_schemas import (
    build_assistant_tool_definitions,
)
from analyses.models import Analysis
from llm import (
    LLMMessage,
    LLMResponse,
    LLMToolDefinition,
)
from llm.providers.anthropic_provider import (
    AnthropicProvider,
)
from llm.providers.openai_provider import (
    OpenAIProvider,
)


@pytest.mark.django_db
def test_assistant_tool_schema_is_read_only_and_typed():
    user = User.objects.create_user(
        username="tool-viewer",
        password="pass12345",
        role=Role.VIEWER,
    )

    tools = (
        build_assistant_tool_definitions(
            user
        )
    )

    assert [
        tool.name
        for tool in tools
    ] == [
        "get_analysis_result"
    ]

    parameters = (
        tools[0].parameters
    )

    assert (
        parameters[
            "properties"
        ][
            "analysis_id"
        ][
            "type"
        ]
        == "integer"
    )

    assert (
        parameters["required"]
        == ["analysis_id"]
    )


@pytest.mark.django_db
def test_agent_runner_executes_allowed_tool():
    user = User.objects.create_user(
        username="tool-analyst",
        password="pass12345",
        role=Role.ANALYST,
    )

    analysis = Analysis.objects.create(
        claim_text="Tool test claim",
        created_by=user,
    )

    class ToolProvider:
        name = "fake-tools"
        model = "fake-model"
        configured = True
        supports_tools = True

        def generate_with_tools(
            self,
            messages,
            *,
            tools,
            tool_executor,
            system=None,
            max_steps=4,
        ):
            assert (
                tools[0].name
                == "get_analysis_result"
            )

            result = tool_executor(
                "get_analysis_result",
                {
                    "analysis_id":
                        analysis.id
                },
            )

            assert (
                result["id"]
                == analysis.id
            )

            return LLMResponse(
                text=(
                    "Analiz sonucu "
                    "tool ile alindi."
                ),
                provider=self.name,
                model=self.model,
                tool_calls=[
                    {
                        "id": "fake-1",
                        "name":
                            "get_analysis_result",
                        "status":
                            "success",
                    }
                ],
            )

    runner = AgentRunner(
        user=user,
        provider=ToolProvider(),
    )

    result = runner.run(
        (
            f"Analysis #{analysis.id} "
            "sonucunu getir."
        )
    )

    assert (
        result.output_text
        == "Analiz sonucu tool ile alindi."
    )

    assert (
        result.tool_calls[0]["name"]
        == "get_analysis_result"
    )


def test_openai_provider_completes_function_call_loop():
    calls = []

    responses = [
        SimpleNamespace(
            id="resp-1",
            output_text="",
            output=[
                SimpleNamespace(
                    type="function_call",
                    call_id="call-1",
                    name=(
                        "get_analysis_result"
                    ),
                    arguments=(
                        '{"analysis_id": 7}'
                    ),
                )
            ],
            usage=SimpleNamespace(
                input_tokens=10,
                output_tokens=3,
            ),
        ),
        SimpleNamespace(
            id="resp-2",
            output_text=(
                "Analysis 7 tamamlandi."
            ),
            output=[],
            usage=SimpleNamespace(
                input_tokens=14,
                output_tokens=6,
            ),
        ),
    ]

    class FakeResponses:
        def create(
            self,
            **kwargs,
        ):
            calls.append(kwargs)

            return responses.pop(0)

    client = SimpleNamespace(
        responses=FakeResponses()
    )

    provider = OpenAIProvider(
        api_key="test",
        model="gpt-4o-mini",
        client=client,
    )

    tool = LLMToolDefinition(
        name="get_analysis_result",
        description="Get analysis",
        parameters={
            "type": "object",
            "properties": {
                "analysis_id": {
                    "type": "integer"
                }
            },
            "required": [
                "analysis_id"
            ],
            "additionalProperties":
                False,
        },
    )

    result = (
        provider.generate_with_tools(
            [
                LLMMessage(
                    role="user",
                    content=(
                        "Analysis 7 nedir?"
                    ),
                )
            ],
            tools=[tool],
            tool_executor=(
                lambda name, args: {
                    "id":
                        args[
                            "analysis_id"
                        ]
                }
            ),
        )
    )

    assert (
        result.text
        == "Analysis 7 tamamlandi."
    )

    assert len(calls) == 2

    assert (
        calls[1]["input"][-1][
            "type"
        ]
        == "function_call_output"
    )

    assert (
        result.tool_calls[0]["status"]
        == "success"
    )


def test_anthropic_provider_completes_tool_use_loop(
    monkeypatch,
):
    calls = []

    class FakeAdapter:
        def __init__(
            self,
            *,
            api_key,
            model,
        ):
            assert api_key == "test"
            assert model == "claude-sonnet-5"

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
                == "Analysis 7 nedir?"
            )

            assert len(tools) == 1

            assert (
                tools[0].name
                == "get_analysis_result"
            )

            tool_result = tool_executor(
                "get_analysis_result",
                {
                    "analysis_id": 7,
                },
            )

            calls.append(
                {
                    "name":
                        "get_analysis_result",
                    "arguments": {
                        "analysis_id": 7,
                    },
                    "result":
                        tool_result,
                }
            )

            return SimpleNamespace(
                text=(
                    "Analysis 7 "
                    "tamamlandi."
                ),
                input_tokens=20,
                output_tokens=9,
                tool_calls=[
                    {
                        "id":
                            "claude-sdk-1",
                        "name":
                            "get_analysis_result",
                        "arguments": {
                            "analysis_id": 7,
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
        api_key="test",
        model="claude-sonnet-5",
    )

    tool = LLMToolDefinition(
        name="get_analysis_result",
        description="Get analysis",
        parameters={
            "type": "object",
            "properties": {
                "analysis_id": {
                    "type": "integer",
                }
            },
            "required": [
                "analysis_id",
            ],
            "additionalProperties":
                False,
        },
    )

    result = (
        provider.generate_with_tools(
            [
                LLMMessage(
                    role="user",
                    content=(
                        "Analysis 7 nedir?"
                    ),
                )
            ],
            tools=[
                tool,
            ],
            tool_executor=(
                lambda name, args: {
                    "id":
                        args[
                            "analysis_id"
                        ],
                }
            ),
        )
    )

    assert (
        result.text
        == "Analysis 7 tamamlandi."
    )

    assert calls == [
        {
            "name":
                "get_analysis_result",
            "arguments": {
                "analysis_id": 7,
            },
            "result": {
                "id": 7,
            },
        }
    ]

    assert (
        result.tool_calls[0]["name"]
        == "get_analysis_result"
    )

    assert (
        result.tool_calls[0]["status"]
        == "success"
    )

    assert (
        result.metadata["agent_sdk"]
        is True
    )

    assert (
        result.metadata["transport"]
        == "claude-agent-sdk"
    )


@pytest.mark.django_db
def test_agent_cannot_read_foreign_analysis():
    owner = User.objects.create_user(
        username="analysis-owner",
        password="pass12345",
        role=Role.ANALYST,
    )

    other = User.objects.create_user(
        username="analysis-other",
        password="pass12345",
        role=Role.ANALYST,
    )

    analysis = Analysis.objects.create(
        claim_text="Private analysis",
        created_by=owner,
    )

    runner = AgentRunner(
        user=other,
        provider=SimpleNamespace(
            name="fake",
            model="fake",
            configured=False,
        ),
    )

    with pytest.raises(
        PermissionError
    ):
        runner.call_tool(
            "get_analysis_result",
            analysis_id=analysis.id,
        )
