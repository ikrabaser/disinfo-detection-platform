from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import (
    IsAnalystOrAdmin,
    IsViewerOrAbove,
)
from analyses.models import (
    Analysis,
    AnalysisStatus,
)
from analyses.serializers import (
    AnalysisCreateSerializer,
    AnalysisSerializer,
)
from procrastinate_app.tasks import (
    run_analysis_task,
)


class AnalysisViewSet(
    viewsets.ModelViewSet
):
    queryset = Analysis.objects.all()
    permission_classes = [
        IsViewerOrAbove
    ]

    def get_serializer_class(self):
        if self.action == "create":
            return AnalysisCreateSerializer

        return AnalysisSerializer

    def get_permissions(self):
        if self.action in (
            "create",
            "update",
            "partial_update",
            "destroy",
            "run",
        ):
            return [
                IsAnalystOrAdmin()
            ]

        return [
            IsViewerOrAbove()
        ]

    def create(
        self,
        request,
        *args,
        **kwargs,
    ):
        """
        Analysis kaydini olusturur ve frontend'e
        tam Analysis nesnesini dondurur.

        Boylece frontend olusan ID'yi alip
        /run/ endpoint'ini cagirabilir.
        """

        serializer = (
            AnalysisCreateSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        analysis = serializer.save(
            created_by=request.user,
            status=AnalysisStatus.PENDING,
        )

        output = AnalysisSerializer(
            analysis
        )

        return Response(
            output.data,
            status=status.HTTP_201_CREATED,
        )

    @action(
        detail=True,
        methods=["post"],
    )
    def run(
        self,
        request,
        pk=None,
    ):
        """
        Analizi PostgreSQL tabanli
        Procrastinate queue'ya gonderir.
        """

        analysis = self.get_object()

        if (
            analysis.status
            == AnalysisStatus.RUNNING
        ):
            return Response(
                {
                    "detail": (
                        "Analiz zaten calisiyor."
                    ),
                    "analysis_id": (
                        analysis.id
                    ),
                },
                status=status.HTTP_409_CONFLICT,
            )

        analysis.status = (
            AnalysisStatus.PENDING
        )

        analysis.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        job = run_analysis_task.defer(
            analysis_id=analysis.id
        )

        return Response(
            {
                "detail": (
                    "Analiz kuyruga eklendi."
                ),
                "analysis_id": (
                    analysis.id
                ),
                "job_id": job.id,
                "status": (
                    analysis.status
                ),
            },
            status=status.HTTP_202_ACCEPTED,
        )
