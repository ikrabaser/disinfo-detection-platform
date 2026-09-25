import pytest

from analyses.models import Analysis, AnalysisStatus


@pytest.mark.django_db
def test_analysis_defaults_to_pending_status():
    analysis = Analysis.objects.create(claim_text="Test iddia metni")
    assert analysis.status == AnalysisStatus.PENDING
    assert analysis.truth_score is None
    assert analysis.ai_analysis_result is None


@pytest.mark.django_db
def test_analysis_str_contains_status_and_id():
    analysis = Analysis.objects.create(claim_text="Baska bir iddia")
    text = str(analysis)
    assert str(analysis.pk) in text
    assert "pending" in text
