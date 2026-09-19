"""GNN model siniflari icin ortak base class.

torch / torch_geometric agir bagimliliklar oldugu icin MODUL YUKLENIRKEN
import edilmez (lazy import). Bu sayede backend, bu kutuphaneler kurulu
olmadan da `python manage.py check` gibi komutlarla calisabilir.
"""
from typing import Any


class BaseGNNModel:
    """Tum GNN model stub'lari (GCN, GAT, GraphSAGE) icin ortak arayuz.

    Gercek implementasyonda bu sinif `torch.nn.Module`'den turetilmelidir:

        import torch.nn as nn
        class BaseGNNModel(nn.Module): ...
    """

    def __init__(self, in_channels: int, hidden_channels: int, out_channels: int, num_layers: int = 2):
        self.in_channels = in_channels
        self.hidden_channels = hidden_channels
        self.out_channels = out_channels
        self.num_layers = num_layers
        self._torch_module = None  # lazy-init edilecek gercek nn.Module (TODO)

    def _lazy_import_torch(self):
        """torch/torch_geometric'i sadece gerektiginde import eder (stub)."""
        try:
            import torch  # noqa: F401
            import torch_geometric  # noqa: F401

            return torch, torch_geometric
        except ImportError as exc:
            raise ImportError(
                "torch ve torch_geometric kurulu degil. Bu proje iskeletinde "
                "GNN inference'i MOCK'lanmistir; gercek egitim/inference icin "
                "requirements.txt icindeki agir ML bagimliliklarini kurun."
            ) from exc

    def forward(self, *args: Any, **kwargs: Any):
        raise NotImplementedError(
            "forward() alt siniflarda (GCNModel, GATModel, GraphSAGEModel) implemente edilmelidir."
        )

    def predict_mock(self) -> dict:
        """Gercek inference yerine kullanilan, sabit/mock bir tahmin doner."""
        return {
            "model": self.__class__.__name__,
            "bot_probability": 0.12,
            "organized_campaign_score": 0.30,
            "note": "MOCK sonuc - gercek GNN inference implement edilmedi (TODO).",
        }
