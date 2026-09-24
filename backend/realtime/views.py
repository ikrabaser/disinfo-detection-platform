from __future__ import annotations

import re

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsViewerOrAbove
from analyses.models import Analysis
from realtime.tokens import (
    create_connection_token,
    create_subscription_token,
)


ANALYSIS_CHANNEL_PATTERN = re.compile(
    r"^analysis:(\d+)$"
)


class CentrifugoConnectTokenView(APIView):
    permission_classes = [
        IsAuthenticated,
        IsViewerOrAbove,
    ]

    def get(self, request):
        token = create_connection_token(
            request.user.pk
        )

        return Response(
            {
                "token": token,
            }
        )


class CentrifugoSubscriptionTokenView(
    APIView
):
    permission_classes = [
        IsAuthenticated,
        IsViewerOrAbove,
    ]

    def post(self, request):
        channel = str(
            request.data.get(
                "channel",
                "",
            )
        ).strip()

        match = (
            ANALYSIS_CHANNEL_PATTERN
            .fullmatch(channel)
        )

        if not match:
            return Response(
                {
                    "detail": (
                        "Gecersiz realtime "
                        "channel."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        analysis_id = int(
            match.group(1)
        )

        if not Analysis.objects.filter(
            pk=analysis_id
        ).exists():
            return Response(
                {
                    "detail": (
                        "Bu analiz kanali "
                        "icin erisim yok."
                    )
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        token = (
            create_subscription_token(
                request.user.pk,
                channel,
            )
        )

        return Response(
            {
                "token": token,
                "channel": channel,
            }
        )


class AnalysisProgressSSEView(APIView):
    """
    SSE fallback endpoint.

    Ana realtime transport Centrifugo
    WebSocket'tir. Bu endpoint su an
    fallback placeholder olarak tutuluyor.
    """

    permission_classes = [
        IsAuthenticated
    ]

    def get(
        self,
        request,
        analysis_id: int,
    ):
        return Response(
            {
                "detail": (
                    "SSE fallback "
                    "aktif degil."
                ),
                "analysis_id":
                    analysis_id,
            }
        )
