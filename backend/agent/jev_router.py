from __future__ import annotations

import logging
from dataclasses import (
    dataclass,
    field,
)

from django.conf import settings

from llm import (
    LLMMessage,
    LLMToolDefinition,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class JevToolRoutingResult:
    tools: list[LLMToolDefinition]

    probabilities: dict[
        str,
        float,
    ] = field(
        default_factory=dict
    )

    used: bool = False
    fallback: bool = False
    reason: str = ""

    model: str | None = None

    def metadata(self) -> dict:
        return {
            "used": self.used,
            "fallback": self.fallback,
            "reason": self.reason,
            "model": self.model,
            "probabilities":
                self.probabilities,
            "selected_tools": [
                tool.name
                for tool in self.tools
            ],
        }


class JevToolRouter:
    """
    Jev tabanli tool shortlist katmani.

    Jev:
        - tool calistirmaz,
        - RBAC karari vermez,
        - tool argument'i uretmez.

    Yalnizca Claude'a hangi izinli tool'larin
    gosterilecegine dair dar bir karar verir.

    Jev kullanilamazsa mevcut VERITAS davranisini
    korumak icin tum izinli tool'lara fallback edilir.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        threshold: float | None = None,
        enabled: bool | None = None,
        client=None,
    ):
        self.api_key = (
            settings.TYPESAFE_API_KEY
            if api_key is None
            else api_key
        )

        self.model = (
            model
            or settings.TYPESAFE_MODEL
        )

        configured_threshold = (
            settings.JEV_TOOL_THRESHOLD
            if threshold is None
            else threshold
        )

        self.threshold = min(
            max(
                float(
                    configured_threshold
                ),
                0.0,
            ),
            1.0,
        )

        self.enabled = (
            settings.JEV_TOOL_ROUTING_ENABLED
            if enabled is None
            else enabled
        )

        self._client = client

    @property
    def configured(self) -> bool:
        return bool(
            self.enabled
            and (
                self.api_key
                or self._client is not None
            )
        )

    @staticmethod
    def _latest_user_message(
        messages: list[LLMMessage],
    ) -> str:
        for message in reversed(
            messages
        ):
            if message.role == "user":
                return message.content

        return ""

    @staticmethod
    def _question_key(
        tool_name: str,
    ) -> str:
        return (
            "tool__"
            + tool_name
        )

    def _fallback(
        self,
        tools: list[
            LLMToolDefinition
        ],
        *,
        reason: str,
    ) -> JevToolRoutingResult:
        return JevToolRoutingResult(
            tools=list(tools),
            used=False,
            fallback=True,
            reason=reason,
            model=self.model,
        )

    def route(
        self,
        messages: list[LLMMessage],
        tools: list[
            LLMToolDefinition
        ],
    ) -> JevToolRoutingResult:
        if not tools:
            return JevToolRoutingResult(
                tools=[],
                used=False,
                fallback=False,
                reason="no_available_tools",
                model=self.model,
            )

        if not self.configured:
            return self._fallback(
                tools,
                reason="jev_not_configured",
            )

        from typesafe_sdk import (
            Noul,
            TypeSafeClient,
        )

        latest_user_message = (
            self._latest_user_message(
                messages
            )
        )

        state = {
            "user_request":
                latest_user_message,
            "available_tools": [
                {
                    "name": tool.name,
                    "description":
                        tool.description,
                }
                for tool in tools
            ],
        }

        questions = {
            self._question_key(
                tool.name
            ): Noul(
                instructions=(
                    "Does answering the user's "
                    "current request materially "
                    "require this VERITAS tool? "
                    f"Tool name: {tool.name}. "
                    "Tool purpose: "
                    f"{tool.description}. "
                    "Answer yes only when the "
                    "tool is actually useful for "
                    "the current request."
                )
            )
            for tool in tools
        }

        owns_client = (
            self._client is None
        )

        client = (
            self._client
            if self._client is not None
            else TypeSafeClient(
                api_key=self.api_key,
                model=self.model,
            )
        )

        try:
            response = (
                client.system_one(
                    state=state,
                    questions=questions,
                )
            )

            probabilities = {
                tool.name: float(
                    response.nouls[
                        self._question_key(
                            tool.name
                        )
                    ].noul
                )
                for tool in tools
            }

            selected = [
                tool
                for tool in tools
                if probabilities[
                    tool.name
                ]
                >= self.threshold
            ]

            return (
                JevToolRoutingResult(
                    tools=selected,
                    probabilities=
                        probabilities,
                    used=True,
                    fallback=False,
                    reason="jev_routed",
                    model=getattr(
                        response,
                        "model",
                        self.model,
                    ),
                )
            )

        except Exception as exc:
            logger.warning(
                "Jev tool routing failed: %s",
                type(exc).__name__,
            )

            return self._fallback(
                tools,
                reason="jev_api_error",
            )

        finally:
            if owns_client:
                client.close()
