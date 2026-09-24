"""Agent tool: run_bot_analysis."""

from bot_engine import inference as bot_inference
from graph_engine.models import PropagationGraph

from agent.tools.permissions import tool_permission


@tool_permission(
    roles={
        "admin",
        "analyst",
    }
)
def run_bot_analysis(
    graph_id: str,
) -> dict:
    """
    Bir propagation graph icindeki benzersiz sosyal medya
    kullanicilari icin profil-feature tabanli bot analizi yapar.

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
        numeric_graph_id = int(
            graph_id
        )

    except (
        TypeError,
        ValueError,
    ) as exc:
        raise ValueError(
            "Gecersiz graph_id: "
            f"{graph_id}"
        ) from exc

    try:
        graph = (
            PropagationGraph.objects
            .get(
                pk=numeric_graph_id
            )
        )

    except PropagationGraph.DoesNotExist as exc:
        raise ValueError(
            "PropagationGraph "
            f"bulunamadi: {graph_id}"
        ) from exc

    result = (
        bot_inference
        .predict_graph_users(
            graph.nodes
        )
    )

    return {
        "graph_id":
            str(graph.pk),

        **result,
    }
