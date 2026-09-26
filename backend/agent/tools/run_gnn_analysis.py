"""Agent tool: run_gnn_analysis."""

from agent.tools.permissions import (
    tool_permission,
)
from analyses.model_result_service import (
    run_and_record_gnn_analysis,
)
from analyses.models import (
    Analysis,
    AnalysisModelRunSource,
)


@tool_permission(
    roles={
        "admin",
        "analyst",
    },
)
def run_gnn_analysis(
    analysis_id: int,
) -> dict:
    """
    Analysis propagation graph'i
    uzerinde GNN inference calistirir.

    Guncel sonucu Analysis.gnn_result
    snapshot'ina ve model run history'ye
    kaydeder.

    Model UPFD Politifact uzerinde
    egitilmistir; Turkce/X kullanimi
    cross-domain deneysel sinyaldir.
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
        run_and_record_gnn_analysis(
            analysis=analysis,
            source=(
                AnalysisModelRunSource
                .AGENT_TOOL
            ),
        )
    )
