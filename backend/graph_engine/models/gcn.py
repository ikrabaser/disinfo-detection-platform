"""GCN (Graph Convolutional Network) model stub.

Gercek implementasyonda torch_geometric.nn.GCNConv katmanlari kullanilarak
haber yayilim grafigi uzerinde node/graph siniflandirmasi yapilacaktir.
"""
from graph_engine.models.base import BaseGNNModel


class GCNModel(BaseGNNModel):
    """Graph Convolutional Network - propagation graph uzerinde node embedding.

    TODO: torch_geometric.nn.GCNConv katmanlarini kullanarak gercek
    implementasyonu yaz. Ornek iskelet:

        from torch_geometric.nn import GCNConv
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, out_channels)
    """

    def forward(self, x=None, edge_index=None):
        """
        Args:
            x: Node feature matrix [num_nodes, in_channels] (torch.Tensor beklenir).
            edge_index: Graph baglantililik matrisi [2, num_edges].

        Returns:
            Mock cikti (gercek egitim yapilmadigi icin sabit deger).
        """
        # Gercek implementasyon torch tensor donerdi; burada mock donuyoruz.
        return self.predict_mock()
