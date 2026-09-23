from __future__ import annotations

import torch
import torch.nn.functional as F

from torch_geometric.nn import (
    GCNConv,
    global_add_pool,
    global_max_pool,
    global_mean_pool,
)


class AlignedGCNClassifier(torch.nn.Module):
    """
    UPFD aligned-profile+structural benchmarkinda egitilen
    GCN mimarisinin inference karsiligi.

    Mimari:
        14D node features
        -> GCNConv(14, 64)
        -> ReLU
        -> Dropout
        -> GCNConv(64, 64)
        -> ReLU
        -> mean + max + add pooling
        -> Linear(192, 2)
    """

    def __init__(
        self,
        in_channels: int = 14,
        hidden_channels: int = 64,
        out_channels: int = 2,
        dropout: float = 0.3,
    ):
        super().__init__()

        self.dropout = dropout

        self.conv1 = GCNConv(
            in_channels,
            hidden_channels,
        )

        self.conv2 = GCNConv(
            hidden_channels,
            hidden_channels,
        )

        self.classifier = torch.nn.Linear(
            hidden_channels * 3,
            out_channels,
        )

    def forward(
        self,
        x,
        edge_index,
        batch,
    ):
        x = self.conv1(
            x,
            edge_index,
        )

        x = F.relu(x)

        x = F.dropout(
            x,
            p=self.dropout,
            training=self.training,
        )

        x = self.conv2(
            x,
            edge_index,
        )

        x = F.relu(x)

        mean_pool = global_mean_pool(
            x,
            batch,
        )

        max_pool = global_max_pool(
            x,
            batch,
        )

        add_pool = global_add_pool(
            x,
            batch,
        )

        graph_embedding = torch.cat(
            [
                mean_pool,
                max_pool,
                add_pool,
            ],
            dim=-1,
        )

        logits = self.classifier(
            graph_embedding
        )

        return {
            "logits": logits,
            "graph_embedding": graph_embedding,
            "node_embeddings": x,
        }
