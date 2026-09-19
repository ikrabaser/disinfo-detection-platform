"""Agent app view'lari - AI ajanini tetiklemek icin API uclari."""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from agent.client import AgentRunner
from agent.tools import TOOL_REGISTRY
from agent.tools.permissions import can_invoke_tool


class AgentPromptView(APIView):
    """Kullanicidan serbest metin promptu alip AgentRunner'i calistirir."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "agent"

    def post(self, request):
        prompt = request.data.get("prompt", "")
        if not prompt:
            return Response({"detail": "'prompt' alani zorunludur."}, status=400)

        runner = AgentRunner(user=request.user)
        result = runner.run(prompt)
        return Response(
            {
                "output_text": result.output_text,
                "tool_calls": result.tool_calls,
                "structured_output": result.structured_output,
            }
        )


class AgentToolListView(APIView):
    """Kullaniciya, rolune gore cagirmaya yetkili oldugu tool listesini doner."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        tools = []
        for name, fn in TOOL_REGISTRY.items():
            meta = getattr(fn, "_tool_meta", {})
            tools.append(
                {
                    "name": name,
                    "description": meta.get("doc", "").splitlines()[0] if meta.get("doc") else "",
                    "allowed_roles": sorted(meta.get("allowed_roles", [])),
                    "can_invoke": can_invoke_tool(request.user, fn),
                }
            )
        return Response({"tools": tools})
