"""Agent tool: run_gnn_analysis."""
from agent.tools.permissions import tool_permission
from graph_engine.graph_builder import mock_propagation_graph_dict
from graph_engine.models import GCNModel


@tool_permission(roles={"admin", "analyst"})
def run_gnn_analysis(graph_id: str) -> dict:
    """Verilen yayilim grafigi (propagation graph) uzerinde GNN analizi calistirir.

    Args:
        graph_id: `graph_engine.models.PropagationGraph` PK'sina karsilik gelen
            kimlik (string olarak gecirilir, tool-calling semasi geregi).

    Returns:
        {
            "graph_id": str,
            "node_count": int,
            "edge_count": int,
            "organized_campaign_score": float,  # 0-1, botlarin organize hareket skoru
            "bot_probability": float,
            "model": str,
        }

    TODO: Gercek implementasyonda `graph_id` ile veritabanindan
    `PropagationGraph` cekilmeli, node/edge listesi torch_geometric.data.Data
    nesnesine cevrilmeli ve egitilmis bir GCN/GAT/GraphSAGE modeli ile
    inference yapilmalidir. Su an tamamen MOCK.
    """
    # MOCK: gercek graph_id ile DB sorgusu yapmiyoruz, sabit bir mock graf kullaniyoruz.
    graph_data = mock_propagation_graph_dict(topic=f"graph-{graph_id}")
    model = GCNModel(in_channels=8, hidden_channels=16, out_channels=2)
    prediction = model.forward()

    return {
        "graph_id": graph_id,
        "node_count": graph_data["node_count"],
        "edge_count": graph_data["edge_count"],
        "organized_campaign_score": prediction["organized_campaign_score"],
        "bot_probability": prediction["bot_probability"],
        "model": prediction["model"],
    }
