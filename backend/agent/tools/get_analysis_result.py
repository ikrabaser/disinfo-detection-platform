"""Agent tool: get_analysis_result."""
from agent.tools.permissions import tool_permission


@tool_permission(roles={"admin", "analyst", "viewer"})
def get_analysis_result(analysis_id: int) -> dict:
    """Veritabaninda saklanan bir analiz sonucunu ID'sine gore getirir.

    Args:
        analysis_id: `analyses.models.Analysis` PK degeri.

    Returns:
        Analysis kaydinin serialize edilmis hali, veya bulunamazsa
        {"error": "..."}.
    """
    # Lazy import - Django app registry hazir olmadan (ör. modul import
    # zincirinde erken cagrildiginda) hata almamak icin fonksiyon icinde import.
    from analyses.models import Analysis
    from analyses.serializers import AnalysisSerializer

    try:
        analysis = Analysis.objects.get(pk=analysis_id)
    except Analysis.DoesNotExist:
        return {"error": f"Analysis id={analysis_id} bulunamadi."}

    return AnalysisSerializer(analysis).data
