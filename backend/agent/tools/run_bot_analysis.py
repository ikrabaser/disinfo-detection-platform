"""Agent tool: run_bot_analysis."""

from agent.tools.permissions import (
    tool_permission,
)
from analyses.model_result_service import (
    run_and_record_bot_analysis,
)
from analyses.models import (
    Analysis,
    AnalysisModelRunSource,
)


@tool_permission(
    roles={
        "admin",
        "analyst",
    }
)
def run_bot_analysis(
    analysis_id: int,
) -> dict:
    """
    Analysis propagation graph'i
    uzerinde profil-feature tabanli
    bot analizi yapar.

    Guncel sonucu
    Analysis.bot_analysis_result
    snapshot'ina ve model run history'ye
    kaydeder.

    Bot skoru kalibre edilmis bir
    olasilik degildir ve modelin guncel
    X verisine uygulanmasi cross-domain
    deneysel sinyaldir.
    """

    try:
        analysis = (
            Analysis.objects
            .select_related(
                "propagation_graph"
            )
            .get(
                pk=analysis_id
            )
        )

    except Analysis.DoesNotExist as exc:
        raise ValueError(
            "Analysis bulunamadi: "
            f"{analysis_id}"
        ) from exc

    return (
        run_and_record_bot_analysis(
            analysis=analysis,
            source=(
                AnalysisModelRunSource
                .AGENT_TOOL
            ),
        )
    )
