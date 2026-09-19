"""
Analysis CRUD/list endpoint'leri. Gercek analiz calistirma islemi (NLP + GNN +
bot analizi tetikleme) `agent` app'i veya `procrastinate_app` gorevleri
uzerinden yapilir; bu view'lar sadece kayit CRUD'u ve tetikleme icin bir
stub saglar.
"""
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsAnalystOrAdmin, IsViewerOrAbove
from analyses.models import Analysis, AnalysisStatus
from analyses.serializers import AnalysisCreateSerializer, AnalysisSerializer


class AnalysisViewSet(viewsets.ModelViewSet):
    queryset = Analysis.objects.all()
    permission_classes = [IsViewerOrAbove]

    def get_serializer_class(self):
        if self.action == "create":
            return AnalysisCreateSerializer
        return AnalysisSerializer

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy", "run"):
            return [IsAnalystOrAdmin()]
        return [IsViewerOrAbove()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, status=AnalysisStatus.PENDING)

    @action(detail=True, methods=["post"])
    def run(self, request, pk=None):
        """
        Analizi (tekrar) calistirmayi tetikler. TODO: gercek implementasyonda
        bu, procrastinate_app.tasks.run_analysis_task.defer(analysis_id=...)
        cagirmali ve Centrifugo uzerinden ilerleme yayinlanmalidir.
        """
        analysis = self.get_object()
        analysis.status = AnalysisStatus.RUNNING
        analysis.save(update_fields=["status"])
        return Response({"detail": "Analiz calistirma tetiklendi (stub).", "analysis_id": analysis.id})
