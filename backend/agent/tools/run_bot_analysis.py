"""Agent tool: run_bot_analysis."""

from agent.tools.permissions import tool_permission
from analyses.models import Analysis
from bot_engine import inference as bot_inference


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
    Verilen VERITAS Analysis kaydinin propagation graph'i
    uzerinde profil-feature tabanli bot analizi yapar.

    Model:
        Random Forest

    Training dataset:
        Cresci-derived TrustNet human/spam subset

    Important:
        Bot skoru kalibre edilmis bir olasilik degildir.
        Model tarihsel Twitter verisi uzerinde egitildigi icin
        guncel X verisine uygulama cross-domain deneysel bir
        model sinyalidir.
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

    result = (
        bot_inference
        .predict_graph_users(
            graph.nodes
        )
    )

    return {
        "analysis_id": analysis.pk,
        "graph_id": str(graph.pk),
        **result,
    }
