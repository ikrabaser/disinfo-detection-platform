"""Agent tool: run_gnn_analysis."""

from agent.tools.permissions import tool_permission
from graph_engine.inference import (
    predict_propagation_graph,
)
from graph_engine.models import (
    PropagationGraph,
)


@tool_permission(
    roles={"admin", "analyst"},
)
def run_gnn_analysis(
    graph_id: str,
) -> dict:
    """
    Verilen propagation graph uzerinde egitilmis
    aligned GCN modeli ile inference calistirir.

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
        graph_pk = int(graph_id)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "graph_id sayisal bir PropagationGraph ID olmali."
        ) from exc

    try:
        graph = PropagationGraph.objects.get(
            pk=graph_pk
        )
    except PropagationGraph.DoesNotExist as exc:
        raise ValueError(
            f"PropagationGraph bulunamadi: {graph_id}"
        ) from exc

    return predict_propagation_graph(
        graph
    )
