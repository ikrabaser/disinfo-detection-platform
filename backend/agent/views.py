from rest_framework.permissions import (
    IsAuthenticated,
)
from rest_framework.response import Response
from rest_framework.throttling import (
    ScopedRateThrottle,
)
from rest_framework.views import APIView

from agent.client import AgentRunner
from agent.tools import TOOL_REGISTRY
from agent.tools.permissions import (
    can_invoke_tool,
)
from llm import get_provider_catalog


class AgentPromptView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    throttle_classes = [
        ScopedRateThrottle
    ]

    throttle_scope = "agent"

    def post(self, request):
        prompt = str(
            request.data.get(
                "prompt",
                "",
            )
        ).strip()

        provider_name = (
            request.data.get(
                "provider"
            )
        )

        if not prompt:
            return Response(
                {
                    "detail":
                        "'prompt' alani zorunludur."
                },
                status=400,
            )

        try:
            runner = AgentRunner(
                user=request.user,
                provider_name=provider_name,
            )

            result = runner.run(
                prompt
            )

        except ValueError as exc:
            return Response(
                {
                    "detail": str(exc)
                },
                status=400,
            )

        return Response(
            {
                "output_text":
                    result.output_text,
                "provider":
                    result.provider,
                "model":
                    result.model,
                "tool_calls":
                    result.tool_calls,
                "structured_output":
                    result.structured_output,
            }
        )


class AgentProviderListView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        return Response(
            {
                "providers":
                    get_provider_catalog()
            }
        )


class AgentToolListView(APIView):
    permission_classes = [
        IsAuthenticated
    ]

    def get(self, request):
        tools = []

        for name, fn in (
            TOOL_REGISTRY.items()
        ):
            meta = getattr(
                fn,
                "_tool_meta",
                {},
            )

            doc = meta.get(
                "doc",
                "",
            )

            tools.append(
                {
                    "name": name,
                    "description": (
                        doc.splitlines()[0]
                        if doc
                        else ""
                    ),
                    "allowed_roles":
                        sorted(
                            meta.get(
                                "allowed_roles",
                                [],
                            )
                        ),
                    "can_invoke":
                        can_invoke_tool(
                            request.user,
                            fn,
                        ),
                }
            )

        return Response(
            {
                "tools": tools
            }
        )
