from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import torch
from django.conf import settings

from graph_engine.aligned_pyg_adapter import (
    propagation_graph_to_aligned_pyg,
)
from graph_engine.models.aligned_gcn import (
    AlignedGCNClassifier,
)


MODEL_NAME = "aligned-gcn-upfd-politifact"

FEATURE_SET = "aligned-profile+structural-14d"

DEFAULT_CHECKPOINT = (
    Path(settings.BASE_DIR)
    / "ml_models"
    / "upfd_aligned"
    / "politifact"
    / "seed_1"
    / "gcn"
    / "model.pt"
)


class GNNInferenceError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def load_gcn_model(
    checkpoint_path: str | None = None,
):
    path = (
        Path(checkpoint_path)
        if checkpoint_path
        else DEFAULT_CHECKPOINT
    )

    if not path.exists():
        raise GNNInferenceError(
            f"GNN checkpoint bulunamadi: {path}"
        )

    checkpoint = torch.load(
        path,
        map_location="cpu",
        weights_only=True,
    )

    model_type = checkpoint.get(
        "model_type"
    )

    if model_type != "gcn":
        raise GNNInferenceError(
            "Checkpoint GCN modeline ait degil: "
            f"{model_type}"
        )

    in_channels = int(
        checkpoint.get(
            "in_channels",
            14,
        )
    )

    hidden_channels = int(
        checkpoint.get(
            "hidden_channels",
            64,
        )
    )

    out_channels = int(
        checkpoint.get(
            "out_channels",
            2,
        )
    )

    pooling = checkpoint.get(
        "pooling",
        "mean",
    )

    if in_channels != 14:
        raise GNNInferenceError(
            "Aligned GCN 14 feature bekliyor, "
            f"checkpoint {in_channels} feature kullaniyor."
        )

    if pooling != "multi":
        raise GNNInferenceError(
            "Aligned GCN checkpoint multi pooling "
            f"kullanmali. Bulunan: {pooling}"
        )

    model = AlignedGCNClassifier(
        in_channels=in_channels,
        hidden_channels=hidden_channels,
        out_channels=out_channels,
    )

    model.load_state_dict(
        checkpoint["state_dict"],
        strict=True,
    )

    model.eval()

    return model


def predict_propagation_graph(
    graph,
) -> dict:
    data = propagation_graph_to_aligned_pyg(
        graph.nodes,
        graph.edges,
    )

    if data.num_node_features != 14:
        raise GNNInferenceError(
            "Beklenmeyen feature sayisi: "
            f"{data.num_node_features}"
        )

    model = load_gcn_model()

    batch = torch.zeros(
        data.num_nodes,
        dtype=torch.long,
    )

    with torch.no_grad():
        output = model(
            x=data.x,
            edge_index=data.edge_index,
            batch=batch,
        )

        probabilities = torch.softmax(
            output["logits"],
            dim=-1,
        )[0]

    fake_probability = float(
        probabilities[0].item()
    )

    real_probability = float(
        probabilities[1].item()
    )

    predicted_index = int(
        probabilities.argmax().item()
    )

    label_map = {
        0: "fake",
        1: "real",
    }

    predicted_label = label_map[
        predicted_index
    ]

    confidence = float(
        probabilities[
            predicted_index
        ].item()
    )

    return {
        "graph_id": str(graph.pk),
        "node_count": data.num_nodes,
        "edge_count": data.num_edges,
        "predicted_label": predicted_label,
        "confidence": round(
            confidence,
            6,
        ),
        "fake_probability": round(
            fake_probability,
            6,
        ),
        "real_probability": round(
            real_probability,
            6,
        ),
        "model": MODEL_NAME,
        "feature_set": FEATURE_SET,
        "benchmark_dataset": "UPFD/politifact",
        "checkpoint_seed": 1,
        "cross_domain": True,
        "note": (
            "Model UPFD Politifact uzerinde egitilmistir. "
            "Turkce/X verisine uygulama cross-domain "
            "deneysel bir sinyaldir."
        ),
    }
