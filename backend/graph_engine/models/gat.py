"""GAT (Graph Attention Network) model stub.

Gercek implementasyonda torch_geometric.nn.GATConv kullanilarak, hangi
kullanicilarin/paylasimlarin yayilimda daha etkili oldugu attention
agirliklariyla ogrenilecektir.
"""
from graph_engine.models.base import BaseGNNModel


class GATModel(BaseGNNModel):
    """Graph Attention Network - attention tabanli yayilim analizi.

    TODO: torch_geometric.nn.GATConv ile gercek implementasyon.
    """

    def __init__(self, in_channels: int, hidden_channels: int, out_channels: int, num_layers: int = 2, heads: int = 4):
        super().__init__(in_channels, hidden_channels, out_channels, num_layers)
        self.heads = heads

    def forward(self, x=None, edge_index=None):
        """Attention agirlikli node/graph tahmini icin stub. Mock sonuc doner."""
        return self.predict_mock()
