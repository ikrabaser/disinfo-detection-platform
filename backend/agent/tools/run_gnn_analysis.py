"""Agent tool: run_gnn_analysis."""

from agent.tools.permissions import tool_permission
from analyses.models import Analysis
from graph_engine.inference import (
    predict_propagation_graph,
)


@tool_permission(
    roles={"admin", "analyst"},
)
def run_gnn_analysis(
    analysis_id: int,
) -> dict:
    """
    Verilen VERITAS Analysis kaydinin propagation graph'i
    uzerinde GCN inference calistirir.

    Model:
        UPFD Politifact
        aligned profile + structural
        14 node feature
        GCN
        multi pooling

    Not:
        Model UPFD uzerinde egitildigi icin
        Turkce/X verisine uygulanmasi cross-domain
        deneysel bir sinyaldir.
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

    graph = analysis.propagation_graph

    if graph is None:
        raise ValueError(
            "Bu Analysis kaydina bagli "
            "propagation graph bulunmuyor."
        )

    result = predict_propagation_graph(
        graph
    )

    model_edge_count = result.get(
        "edge_count"
    )

    return {
        "analysis_id": analysis.pk,
        **result,
        "edge_count": len(
            graph.edges or []
        ),
        "model_edge_count":
            model_edge_count,
    }
