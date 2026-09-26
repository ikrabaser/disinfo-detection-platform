from types import SimpleNamespace

from llm.schemas import (
    LLMResponse,
    LLMToolDefinition,
)

from ai_analysis import deep_agent


class FakeUser:
    id = 7
    role = "analyst"
    is_authenticated = True


class FakeRunner:
    def __init__(
        self,
        *,
        user,
        provider,
    ):
        self.user = user
        self.provider = provider

    def call_tool(
        self,
        name,
        **arguments,
    ):
        return {
            "tool": name,
            "arguments": arguments,
        }


class FakeProvider:
    name = "anthropic"
    model = "claude-test"
    configured = True

    def generate_with_tools(
        self,
        messages,
        *,
        tools,
        tool_executor,
        system=None,
        max_steps=4,
    ):
        assert system
        assert max_steps == 6

        assert {
            tool.name
            for tool in tools
        } == {
            "get_analysis_result",
            "search_evidence",
        }

        return LLMResponse(
            text="Deep review tamamlandi.",
            provider=self.name,
            model=self.model,
            tool_calls=[
                {
                    "name":
                        "get_analysis_result",
                    "status":
                        "success",
                },
                {
                    "name":
                        "search_evidence",
                    "status":
                        "success",
                },
            ],
            metadata={
                "transport":
                    "claude-agent-sdk",
                "agent_sdk": True,
            },
        )


def fake_tool_definitions(
    user,
):
    return [
        LLMToolDefinition(
            name=
                "get_analysis_result",
            description="Analysis getir",
            parameters={
                "type": "object",
            },
        ),
        LLMToolDefinition(
            name=
                "search_evidence",
            description="Evidence ara",
            parameters={
                "type": "object",
            },
        ),
        LLMToolDefinition(
            name=
                "run_gnn_analysis",
            description="GNN calistir",
            parameters={
                "type": "object",
            },
        ),
    ]


def test_deep_agent_review_uses_only_read_tools(
    monkeypatch,
):
    monkeypatch.setattr(
        deep_agent,
        "AgentRunner",
        FakeRunner,
    )

    monkeypatch.setattr(
        deep_agent,
        "build_assistant_tool_definitions",
        fake_tool_definitions,
    )

    analysis = SimpleNamespace(
        id=42,
        claim_text="Test claim",
        created_by=FakeUser(),
    )

    result = (
        deep_agent
        .run_deep_agent_review(
            analysis=analysis,
            provider=FakeProvider(),
            structured_result={
                "status":
                    "completed",
                "report": {
                    "overall_evidence_status":
                        "insufficient",
                    "claims": [],
                    "assessments": [],
                    "evidence": {},
                    "limitations": [],
                },
            },
            max_steps=6,
        )
    )

    assert (
        result["status"]
        == "completed"
    )

    assert (
        result["transport"]
        == "claude-agent-sdk"
    )

    assert (
        result[
            "tool_call_count"
        ]
        == 2
    )


def test_deep_agent_review_requires_owner():
    analysis = SimpleNamespace(
        id=42,
        claim_text="Test claim",
        created_by=None,
    )

    result = (
        deep_agent
        .run_deep_agent_review(
            analysis=analysis,
            provider=FakeProvider(),
            structured_result={},
        )
    )

    assert (
        result["status"]
        == "unavailable"
    )

    assert (
        result["reason"]
        == "analysis_owner_missing"
    )


def test_deep_agent_review_retries_provider_error(
    monkeypatch,
):
    calls = {
        "count": 0,
    }

    sleeps = []

    def fake_run(
        **kwargs,
    ):
        calls["count"] += 1

        if calls["count"] == 1:
            raise (
                deep_agent
                .LLMProviderError(
                    "temporary"
                )
            )

        return {
            "status":
                "completed",
            "transport":
                "claude-agent-sdk",
        }

    monkeypatch.setattr(
        deep_agent,
        "run_deep_agent_review",
        fake_run,
    )

    result = (
        deep_agent
        .run_deep_agent_review_with_retry(
            analysis=object(),
            provider=object(),
            structured_result={},
            max_steps=6,
            retry_delays=(0.0,),
            sleep_fn=sleeps.append,
        )
    )

    assert (
        calls["count"]
        == 2
    )

    assert sleeps == [
        0.0
    ]

    assert (
        result["status"]
        == "completed"
    )

    assert (
        result["attempt_count"]
        == 2
    )

    assert (
        result["retry_count"]
        == 1
    )
