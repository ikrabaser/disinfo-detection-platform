from __future__ import annotations

from graph_engine.models.base import BaseGNNModel


class GCNModel(BaseGNNModel):
    def __init__(
        self,
        in_channels: int,
        hidden_channels: int,
        out_channels: int,
        num_layers: int = 2,
        dropout: float = 0.30,
    ):
        super().__init__(
            in_channels=in_channels,
            hidden_channels=hidden_channels,
            out_channels=out_channels,
            num_layers=num_layers,
        )

        self.dropout = dropout

    def _build_model(self):
        if self._torch_module is not None:
            return

        torch, _ = self._lazy_import_torch()

        from torch_geometric.nn import (
            GCNConv,
            global_mean_pool,
        )

        class Network(torch.nn.Module):
            def __init__(
                self,
                in_channels: int,
                hidden_channels: int,
                out_channels: int,
                dropout: float,
            ):
                super().__init__()

                self.conv1 = GCNConv(
                    in_channels,
                    hidden_channels,
                )

                self.conv2 = GCNConv(
                    hidden_channels,
                    hidden_channels,
                )

                self.classifier = (
                    torch.nn.Linear(
                        hidden_channels,
                        out_channels,
                    )
                )

                self.dropout = dropout

            def forward(
                self,
                x,
                edge_index,
                batch=None,
            ):
                if batch is None:
                    batch = torch.zeros(
                        x.size(0),
                        dtype=torch.long,
                        device=x.device,
                    )

                x = self.conv1(
                    x,
                    edge_index,
                )

                x = torch.relu(x)

                x = torch.dropout(
                    x,
                    p=self.dropout,
                    train=self.training,
                )

                x = self.conv2(
                    x,
                    edge_index,
                )

                x = torch.relu(x)

                graph_embedding = (
                    global_mean_pool(
                        x,
                        batch,
                    )
                )

                logits = self.classifier(
                    graph_embedding
                )

                return {
                    "logits": logits,
                    "graph_embedding": (
                        graph_embedding
                    ),
                    "node_embeddings": x,
                }

        self._torch_module = Network(
            in_channels=self.in_channels,
            hidden_channels=self.hidden_channels,
            out_channels=self.out_channels,
            dropout=self.dropout,
        )

    def forward(
        self,
        x,
        edge_index,
        batch=None,
    ):
        self._build_model()

        return self._torch_module(
            x=x,
            edge_index=edge_index,
            batch=batch,
        )

    def eval(self):
        self._build_model()
        self._torch_module.eval()
        return self

    def train(self):
        self._build_model()
        self._torch_module.train()
        return self

    def parameters(self):
        self._build_model()
        return self._torch_module.parameters()
