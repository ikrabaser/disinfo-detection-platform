from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import Role
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
    AnalysisModelRunSerializer,
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

    def get_queryset(self):
        """
        Analysis kayitlarini kullanici scope'una
        gore sinirlar.

        Admin tum kayitlari gorebilir.
        Diger roller yalniz kendi kayitlarini
        gorebilir.
        """

        queryset = (
            Analysis.objects
            .all()
        )

        user = self.request.user

        if (
            getattr(
                user,
                "role",
                None,
            )
            == Role.ADMIN
        ):
            return queryset

        return queryset.filter(
            created_by=user
        )

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
        detail=False,
        methods=["get"],
        url_path="dashboard-summary",
    )
    def dashboard_summary(
        self,
        request,
    ):
        """
        Dashboard icin kullanicinin yetki
        kapsamindaki gercek Analysis
        kayitlarinin ozetini dondurur.
        """

        queryset = self.get_queryset()

        counts = {
            "total":
                queryset.count(),
            "pending":
                queryset.filter(
                    status=AnalysisStatus.PENDING
                ).count(),
            "running":
                queryset.filter(
                    status=AnalysisStatus.RUNNING
                ).count(),
            "completed":
                queryset.filter(
                    status=AnalysisStatus.COMPLETED
                ).count(),
            "failed":
                queryset.filter(
                    status=AnalysisStatus.FAILED
                ).count(),
        }

        latest_analysis = (
            queryset
            .order_by(
                "-created_at",
                "-id",
            )
            .first()
        )

        latest_data = (
            AnalysisSerializer(
                latest_analysis
            ).data
            if latest_analysis
            else None
        )

        return Response(
            {
                "counts": counts,
                "latest_analysis":
                    latest_data,
            }
        )

    @action(
        detail=True,
        methods=["get"],
        url_path="model-runs",
    )
    def model_runs(
        self,
        request,
        pk=None,
    ):
        """
        Analysis icin immutable model
        inference history'sini dondurur.

        get_object() kullanildigi icin
        get_queryset ownership scope'u
        burada da uygulanir.
        """

        analysis = self.get_object()

        runs = (
            analysis.model_runs
            .all()
            .order_by(
                "-generated_at",
                "-id",
            )
        )

        serializer = (
            AnalysisModelRunSerializer(
                runs,
                many=True,
            )
        )

        return Response(
            serializer.data
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

        job_id = run_analysis_task.defer(
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
                "job_id": job_id,
                "status": (
                    analysis.status
                ),
            },
            status=status.HTTP_202_ACCEPTED,
        )
