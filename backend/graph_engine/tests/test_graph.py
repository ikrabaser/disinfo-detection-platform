import pytest

from graph_engine.graph_builder import mock_propagation_graph_dict
from graph_engine.models import GATModel, GCNModel, GraphSAGEModel, PropagationGraph


def test_mock_propagation_graph_has_nodes_and_edges():
    result = mock_propagation_graph_dict(topic="test-konu")
    assert result["node_count"] == 4
    assert result["edge_count"] == 3
    assert result["topic"] == "test-konu"


def test_gnn_model_stubs_return_mock_predictions():
    for model_cls in (GCNModel, GATModel, GraphSAGEModel):
        model = model_cls(in_channels=8, hidden_channels=16, out_channels=2)
        result = model.forward()
        assert "bot_probability" in result
        assert result["model"] == model_cls.__name__


@pytest.mark.django_db
def test_propagation_graph_model_creates_and_str():
    graph = PropagationGraph.objects.create(node_count=4, edge_count=3, nodes=[], edges=[])
    assert "PropagationGraph" in str(graph)
    assert graph.node_count == 4
