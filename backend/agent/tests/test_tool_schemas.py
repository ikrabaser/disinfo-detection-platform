from agent.tool_schemas import (
    build_assistant_tool_definitions,
)


class FakeAnalyst:
    is_authenticated = True
    role = "analyst"


def test_search_evidence_limit_is_integer():
    tools = (
        build_assistant_tool_definitions(
            FakeAnalyst()
        )
    )

    search_tool = next(
        tool
        for tool in tools
        if tool.name
        == "search_evidence"
    )

    assert (
        search_tool.parameters[
            "properties"
        ][
            "limit"
        ][
            "type"
        ]
        == "integer"
    )
