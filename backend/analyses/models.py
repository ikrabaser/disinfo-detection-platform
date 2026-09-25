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
