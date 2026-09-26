"""
Bu app'in `Analysis` modeli, platformun kalbidir: bir haber/iddia (article
veya claim) icin yapilan NLP, GNN ve bot analizi sonuclarini ve nihai
"truth score" (dogruluk skoru) degerini bir arada tutar.

pgvector NOTU (opsiyonel, calistirilmasi gerekmez):
    Haber metninin semantik embedding'ini saklamak icin asagidaki gibi bir
    alan eklenebilir (pgvector extension + django-pgvector kurulduktan sonra):

        # from pgvector.django import VectorField
        # embedding = VectorField(dimensions=384, null=True, blank=True)

    Migration ornegi:
        # migrations.RunSQL("CREATE EXTENSION IF NOT EXISTS vector;")

    Bu proje iskeletinde bu alan devre disi birakilmistir.
"""
from django.conf import settings
from django.db import models


class AnalysisStatus(models.TextChoices):
    PENDING = "pending", "Beklemede"
    RUNNING = "running", "Calisiyor"
    COMPLETED = "completed", "Tamamlandi"
    FAILED = "failed", "Basarisiz"


class Analysis(models.Model):
    """Bir haber/iddia icin yapilan uctan uca dezenformasyon analizi."""

    # Girdi
    claim_text = models.TextField(help_text="Analiz edilecek haber metni / iddia.")
    source_url = models.URLField(blank=True, null=True)
    query = models.CharField(
        max_length=255, blank=True, help_text="Sosyal medya/haber aramasinda kullanilan sorgu."
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="analyses"
    )
    status = models.CharField(max_length=20, choices=AnalysisStatus.choices, default=AnalysisStatus.PENDING)

    # Alt sonuclar - her biri ilgili tool/app tarafindan doldurulan JSON alanlari.
    nlp_result = models.JSONField(
        null=True, blank=True, help_text="nlp_engine tarafindan uretilen semantik/siniflandirma sonucu."
    )
    gnn_result = models.JSONField(
        null=True, blank=True, help_text="graph_engine tarafindan uretilen yayilim grafigi analiz sonucu."
    )
    bot_analysis_result = models.JSONField(
        null=True, blank=True, help_text="Bot/organize davranis tespiti sonucu (kullanici bazli skorlar)."
    )
    ai_analysis_result = models.JSONField(
        null=True,
        blank=True,
        help_text=(
            "Claim extraction, evidence retrieval, "
            "RAG, evidence reasoning ve manipulation "
            "analysis sonucunu tutar."
        ),
    )
    source_verification_result = models.JSONField(
        null=True, blank=True, help_text="verify_sources tool'undan gelen kaynak dogrulama sonucu."
    )

    # Nihai skor
    truth_score = models.FloatField(
        null=True,
        blank=True,
        help_text="0.0 (kesin sahte) - 1.0 (kesin dogru) arasinda birlestirilmis dogruluk skoru.",
    )

    propagation_graph = models.ForeignKey(
        "graph_engine.PropagationGraph",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="analyses",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "analyses"

    def __str__(self) -> str:
        preview = (self.claim_text or "")[:50]
        return f"Analysis #{self.pk} [{self.status}] {preview}"


class AnalysisModelRunKind(
    models.TextChoices
):
    GNN = "gnn", "GNN"
    BOT = "bot", "Bot"


class AnalysisModelRunSource(
    models.TextChoices
):
    PIPELINE = (
        "pipeline",
        "Analysis Pipeline",
    )
    AGENT_TOOL = (
        "agent_tool",
        "Agent Tool",
    )
    LEGACY_IMPORT = (
        "legacy_import",
        "Legacy Import",
    )


class AnalysisModelRun(models.Model):
    """
    Bir Analysis icin model inference
    calismasinin immutable history kaydi.

    Analysis.gnn_result ve
    Analysis.bot_analysis_result halen
    current snapshot olarak tutulur.
    """

    analysis = models.ForeignKey(
        Analysis,
        on_delete=models.CASCADE,
        related_name="model_runs",
    )

    kind = models.CharField(
        max_length=16,
        choices=
            AnalysisModelRunKind.choices,
    )

    source = models.CharField(
        max_length=32,
        choices=
            AnalysisModelRunSource.choices,
    )

    model_name = models.CharField(
        max_length=255,
        blank=True,
    )

    feature_set = models.CharField(
        max_length=255,
        blank=True,
    )

    graph_id_snapshot = (
        models.BigIntegerField(
            null=True,
            blank=True,
        )
    )

    artifact_ref = models.CharField(
        max_length=500,
        blank=True,
    )

    result = models.JSONField(
        default=dict,
    )

    cross_domain = (
        models.BooleanField(
            default=False,
        )
    )

    generated_at = (
        models.DateTimeField(
            auto_now_add=True,
        )
    )

    class Meta:
        ordering = [
            "-generated_at",
            "-id",
        ]

        indexes = [
            models.Index(
                fields=[
                    "analysis",
                    "kind",
                    "-generated_at",
                ],
                name=(
                    "analysis_run_lookup"
                ),
            )
        ]

    def __str__(self) -> str:
        return (
            f"AnalysisModelRun "
            f"#{self.pk} "
            f"analysis={self.analysis_id} "
            f"kind={self.kind} "
            f"model={self.model_name}"
        )

