from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


LLMRole = Literal[
    "user",
    "assistant",
]


@dataclass(slots=True)
class LLMMessage:
    role: LLMRole
    content: str

    def as_dict(self) -> dict[str, str]:
        return {
            "role": self.role,
            "content": self.content,
        }


@dataclass(slots=True)
class LLMToolDefinition:
    name: str
    description: str
    parameters: dict[str, Any]


@dataclass(slots=True)
class LLMResponse:
    text: str
    provider: str
    model: str

    input_tokens: int | None = None
    output_tokens: int | None = None

    tool_calls: list[
        dict[str, Any]
    ] = field(
        default_factory=list
    )

    metadata: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass(slots=True)
class LLMStreamEvent:
    type: Literal[
        "delta",
        "tool_start",
        "tool_end",
        "done",
    ]

    delta: str = ""

    tool_call: (
        dict[str, Any] | None
    ) = None

    response: (
        LLMResponse | None
    ) = None
