"""GraphSAGE model stub.

Gercek implementasyonda torch_geometric.nn.SAGEConv kullanilarak buyuk
olcekli (inductive) graf ornekleme/agregasyon yapilacaktir - yeni
kullanicilar/paylasimlar geldiginde yeniden egitime gerek kalmadan
tahmin uretebilmek icin uygundur.
"""
from graph_engine.models.base import BaseGNNModel


class GraphSAGEModel(BaseGNNModel):
    """GraphSAGE - inductive node embedding / komsu ornekleme.

    TODO: torch_geometric.nn.SAGEConv ile gercek implementasyon.
    """

    def forward(self, x=None, edge_index=None):
        """Komsu ornekleme + agregasyon stub. Mock sonuc doner."""
        return self.predict_mock()
