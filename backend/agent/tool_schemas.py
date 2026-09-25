from __future__ import annotations

import inspect
from typing import Any

from agent.tools import TOOL_REGISTRY
from agent.tools.permissions import (
    can_invoke_tool,
)
from llm import LLMToolDefinition


# Ilk agentic milestone:
# yalnizca read-only ve gercek veriye dayanan
# tool modele otomatik olarak aciliyor.
ASSISTANT_TOOL_NAMES = {
    "get_analysis_result",
}


def _parameter_schema(
    annotation: Any,
) -> dict[str, Any]:
    if annotation is int:
        return {
            "type": "integer"
        }

    if annotation is float:
        return {
            "type": "number"
        }

    if annotation is bool:
        return {
            "type": "boolean"
        }

    return {
        "type": "string"
    }


def _description(
    fn,
) -> str:
    doc = inspect.getdoc(fn) or ""

    if not doc:
        return fn.__name__

    return doc.splitlines()[0]


def build_assistant_tool_definitions(
    user,
) -> list[LLMToolDefinition]:
    definitions: list[
        LLMToolDefinition
    ] = []

    for name in sorted(
        ASSISTANT_TOOL_NAMES
    ):
        fn = TOOL_REGISTRY.get(
            name
        )

        if fn is None:
            continue

        if not can_invoke_tool(
            user,
            fn,
        ):
            continue

        signature = inspect.signature(
            fn
        )

        properties = {}
        required = []

        for (
            parameter_name,
            parameter,
        ) in signature.parameters.items():
            if (
                parameter.kind
                in {
                    inspect.Parameter
                    .VAR_POSITIONAL,
                    inspect.Parameter
                    .VAR_KEYWORD,
                }
            ):
                continue

            schema = (
                _parameter_schema(
                    parameter.annotation
                )
            )

            if (
                parameter.default
                is not
                inspect.Parameter.empty
            ):
                schema["default"] = (
                    parameter.default
                )
            else:
                required.append(
                    parameter_name
                )

            properties[
                parameter_name
            ] = schema

        definitions.append(
            LLMToolDefinition(
                name=name,
                description=(
                    _description(fn)
                ),
                parameters={
                    "type": "object",
                    "properties":
                        properties,
                    "required":
                        required,
                    "additionalProperties":
                        False,
                },
            )
        )

    return definitions
