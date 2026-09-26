from types import SimpleNamespace

from agent.jev_router import (
    JevToolRouter,
)
from llm import (
    LLMMessage,
    LLMToolDefinition,
)


def make_tool(
    name: str,
) -> LLMToolDefinition:
    return LLMToolDefinition(
        name=name,
        description=(
            f"{name} test tool"
        ),
        parameters={
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties":
                False,
        },
    )


def test_jev_router_falls_back_when_not_configured(
    settings,
):
    settings.TYPESAFE_API_KEY = ""
    settings.JEV_TOOL_ROUTING_ENABLED = False

    tools = [
        make_tool(
            "search_evidence"
        ),
        make_tool(
            "run_gnn_analysis"
        ),
    ]

    router = JevToolRouter()

    result = router.route(
        [
            LLMMessage(
                role="user",
                content="Bu iddiayi analiz et.",
            )
        ],
        tools,
    )

    assert result.fallback is True
    assert result.used is False

    assert [
        tool.name
        for tool in result.tools
    ] == [
        "search_evidence",
        "run_gnn_analysis",
    ]


def test_jev_router_selects_multiple_tools():
    class FakeClient:
        def system_one(
            self,
            *,
            state,
            questions,
        ):
            assert (
                state["user_request"]
                == "Analysis #4 icin "
                "GNN ve bot analizi yap."
            )

            assert (
                "tool__run_gnn_analysis"
                in questions
            )

            return SimpleNamespace(
                model="jev-test",
                nouls={
                    "tool__search_evidence":
                        SimpleNamespace(
                            noul=0.18
                        ),
                    "tool__run_gnn_analysis":
                        SimpleNamespace(
                            noul=0.94
                        ),
                    "tool__run_bot_analysis":
                        SimpleNamespace(
                            noul=0.91
                        ),
                },
            )

    tools = [
        make_tool(
            "search_evidence"
        ),
        make_tool(
            "run_gnn_analysis"
        ),
        make_tool(
            "run_bot_analysis"
        ),
    ]

    router = JevToolRouter(
        client=FakeClient(),
        enabled=True,
        threshold=0.70,
        model="jev-test",
    )

    result = router.route(
        [
            LLMMessage(
                role="user",
                content=(
                    "Analysis #4 icin "
                    "GNN ve bot analizi yap."
                ),
            )
        ],
        tools,
    )

    assert result.used is True
    assert result.fallback is False

    assert [
        tool.name
        for tool in result.tools
    ] == [
        "run_gnn_analysis",
        "run_bot_analysis",
    ]

    assert (
        result.probabilities[
            "run_gnn_analysis"
        ]
        == 0.94
    )


import pytest

from accounts.models import (
    Role,
    User,
)
from agent.client import AgentRunner
from agent.jev_router import (
    JevToolRoutingResult,
)
from llm import LLMResponse


class FakeRoutedProvider:
    name = "fake-routed"
    model = "fake-model"
    configured = True
    supports_tools = True

    def __init__(self):
        self.tool_names = []

    def generate_with_tools(
        self,
        messages,
        *,
        tools,
        tool_executor,
        system=None,
        max_steps=4,
    ):
        self.tool_names = [
            tool.name
            for tool in tools
        ]

        return LLMResponse(
            text="Routed response",
            provider=self.name,
            model=self.model,
            metadata={},
        )

    def generate(
        self,
        messages,
        *,
        system=None,
    ):
        return LLMResponse(
            text="No-tool response",
            provider=self.name,
            model=self.model,
            metadata={},
        )


@pytest.mark.django_db
def test_agent_runner_uses_jev_shortlist():
    user = User.objects.create_user(
        username="jev-analyst",
        password="pass12345",
        role=Role.ANALYST,
    )

    class FakeRouter:
        def route(
            self,
            messages,
            tools,
        ):
            selected = [
                tool
                for tool in tools
                if tool.name
                == "run_gnn_analysis"
            ]

            return JevToolRoutingResult(
                tools=selected,
                probabilities={
                    "run_gnn_analysis":
                        0.96,
                },
                used=True,
                fallback=False,
                reason="jev_routed",
                model="jev-test",
            )

    provider = FakeRoutedProvider()

    runner = AgentRunner(
        user=user,
        provider=provider,
        tool_router=FakeRouter(),
    )

    result = runner.run(
        "Analysis #4 yayilim "
        "modelini incele."
    )

    assert provider.tool_names == [
        "run_gnn_analysis"
    ]

    metadata = (
        result.structured_output[
            "metadata"
        ][
            "jev_router"
        ]
    )

    assert metadata["used"] is True

    assert metadata[
        "selected_tools"
    ] == [
        "run_gnn_analysis"
    ]


@pytest.mark.django_db
def test_rbac_filters_tools_before_jev():
    viewer = User.objects.create_user(
        username="jev-viewer",
        password="pass12345",
        role=Role.VIEWER,
    )

    seen_tool_names = []

    class InspectingRouter:
        def route(
            self,
            messages,
            tools,
        ):
            seen_tool_names.extend(
                tool.name
                for tool in tools
            )

            return JevToolRoutingResult(
                tools=list(tools),
                used=True,
                fallback=False,
                reason="jev_routed",
                model="jev-test",
            )

    provider = FakeRoutedProvider()

    runner = AgentRunner(
        user=viewer,
        provider=provider,
        tool_router=InspectingRouter(),
    )

    runner.run(
        "Analysis sonucunu acikla."
    )

    assert seen_tool_names == [
        "get_analysis_result"
    ]

    assert (
        "run_gnn_analysis"
        not in seen_tool_names
    )

    assert (
        "run_bot_analysis"
        not in seen_tool_names
    )

    assert (
        "search_evidence"
        not in seen_tool_names
    )
