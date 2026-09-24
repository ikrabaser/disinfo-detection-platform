import pytest
import torch

from graph_engine.graph_builder import (
    mock_propagation_graph_dict,
)
from graph_engine.models import (
    GATModel,
    GCNModel,
    GraphSAGEModel,
    PropagationGraph,
)


def test_mock_propagation_graph_has_nodes_and_edges():
    result = mock_propagation_graph_dict(
        topic="test-konu"
    )

    assert result["node_count"] == 4
    assert result["edge_count"] == 3
    assert result["topic"] == "test-konu"


def test_gcn_model_runs_real_forward_pass():
    model = GCNModel(
        in_channels=8,
        hidden_channels=16,
        out_channels=2,
    )

    x = torch.randn(
        4,
        8,
    )

    edge_index = torch.tensor(
        [
            [0, 1, 2],
            [1, 2, 3],
        ],
        dtype=torch.long,
    )

    result = model.forward(
        x=x,
        edge_index=edge_index,
    )

    assert "logits" in result
    assert "graph_embedding" in result
    assert "node_embeddings" in result

    assert result["logits"].shape == (
        1,
        2,
    )

    assert result[
        "graph_embedding"
    ].shape == (
        1,
        16,
    )

    assert result[
        "node_embeddings"
    ].shape == (
        4,
        16,
    )


def test_remaining_gnn_stub_models_return_mock_predictions():
    for model_cls in (
        GATModel,
        GraphSAGEModel,
    ):
        model = model_cls(
            in_channels=8,
            hidden_channels=16,
            out_channels=2,
        )

        result = model.forward()

        assert (
            "bot_probability"
            in result
        )

        assert (
            result["model"]
            == model_cls.__name__
        )


@pytest.mark.django_db
def test_propagation_graph_model_creates_and_str():
    graph = (
        PropagationGraph.objects.create(
            node_count=4,
            edge_count=3,
            nodes=[],
            edges=[],
        )
    )

    assert (
        "PropagationGraph"
        in str(graph)
    )

    assert graph.node_count == 4
