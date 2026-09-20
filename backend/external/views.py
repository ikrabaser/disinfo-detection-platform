from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsAnalystOrAdmin, IsViewerOrAbove
from external.services import fetch_social_posts, ingest_social_query


class SocialSearchView(APIView):
    permission_classes = [IsViewerOrAbove]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        max_results = request.query_params.get("max_results", 10)

        try:
            result = fetch_social_posts(
                query=query,
                max_results=int(max_results),
            )
        except (TypeError, ValueError) as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(result)


class SocialIngestView(APIView):
    permission_classes = [IsAnalystOrAdmin]

    def post(self, request):
        query = str(request.data.get("query", "")).strip()
        max_results = request.data.get("max_results", 10)

        try:
            result = ingest_social_query(
                query=query,
                max_results=int(max_results),
            )
        except (TypeError, ValueError) as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            result,
            status=status.HTTP_201_CREATED,
        )
