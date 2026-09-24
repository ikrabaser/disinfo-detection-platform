from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

BACKEND_ROOT = Path(__file__).resolve().parents[1]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from torch_geometric.datasets import UPFD

from graph_engine.structural_features import (
    build_structural_features,
)


LABEL_NAMES = [
    "fake",
    "real",
]


def graph_features(data):
    x = build_structural_features(
        edge_index=data.edge_index,
        num_nodes=data.num_nodes,
    )

    num_nodes = float(
        data.num_nodes
    )

    num_edges = float(
        data.num_edges
    )

    in_degree_log = x[:, 0]
    out_degree_log = x[:, 1]
    total_degree_log = x[:, 2]
    is_root = x[:, 3]
    is_leaf = x[:, 4]
    depth_log = x[:, 5]

    non_leaf_mask = (
        is_leaf == 0
    )

    if non_leaf_mask.any():
        branching_mean = (
            out_degree_log[
                non_leaf_mask
            ]
            .mean()
            .item()
        )
    else:
        branching_mean = 0.0

    return [
        math.log1p(num_nodes),
        math.log1p(num_edges),

        float(
            in_degree_log.mean().item()
        ),
        float(
            in_degree_log.max().item()
        ),

        float(
            out_degree_log.mean().item()
        ),
        float(
            out_degree_log.max().item()
        ),

        float(
            total_degree_log.mean().item()
        ),
        float(
            total_degree_log.max().item()
        ),

        float(
            is_root.mean().item()
        ),

        float(
            is_leaf.mean().item()
        ),

        float(
            depth_log.mean().item()
        ),
        float(
            depth_log.max().item()
        ),

        float(branching_mean),
    ]


def dataset_to_xy(dataset):
    features = []
    labels = []

    for data in dataset:
        features.append(
            graph_features(data)
        )

        labels.append(
            int(data.y.item())
        )

    return (
        np.asarray(
            features,
            dtype=np.float32,
        ),
        np.asarray(
            labels,
            dtype=np.int64,
        ),
    )


def evaluate(
    model,
    x,
    y,
    name,
):
    predictions = model.predict(x)

    accuracy = accuracy_score(
        y,
        predictions,
    )

    macro_f1 = f1_score(
        y,
        predictions,
        average="macro",
    )

    print()
    print("=" * 60)
    print(name)
    print("=" * 60)

    print(
        f"accuracy={accuracy:.4f}"
    )

    print(
        f"macro_f1={macro_f1:.4f}"
    )

    print()

    print(
        classification_report(
            y,
            predictions,
            labels=[0, 1],
            target_names=LABEL_NAMES,
            zero_division=0,
        )
    )

    print(
        "Confusion Matrix:"
    )

    print(
        confusion_matrix(
            y,
            predictions,
            labels=[0, 1],
        )
    )


def main():
    root = (
        Path("ml_data")
        / "UPFD"
    )

    train_dataset = UPFD(
        root=str(root),
        name="politifact",
        feature="profile",
        split="train",
    )

    val_dataset = UPFD(
        root=str(root),
        name="politifact",
        feature="profile",
        split="val",
    )

    test_dataset = UPFD(
        root=str(root),
        name="politifact",
        feature="profile",
        split="test",
    )

    x_train, y_train = (
        dataset_to_xy(
            train_dataset
        )
    )

    x_val, y_val = (
        dataset_to_xy(
            val_dataset
        )
    )

    x_test, y_test = (
        dataset_to_xy(
            test_dataset
        )
    )

    print(
        "Train shape:",
        x_train.shape,
    )

    print(
        "Val shape:",
        x_val.shape,
    )

    print(
        "Test shape:",
        x_test.shape,
    )

    print(
        "Train labels:",
        np.bincount(y_train),
    )

    print(
        "Val labels:",
        np.bincount(y_val),
    )

    print(
        "Test labels:",
        np.bincount(y_test),
    )

    model = Pipeline(
        [
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=42,
                ),
            ),
        ]
    )

    model.fit(
        x_train,
        y_train,
    )

    evaluate(
        model,
        x_val,
        y_val,
        "VALIDATION",
    )

    evaluate(
        model,
        x_test,
        y_test,
        "TEST",
    )


if __name__ == "__main__":
    main()
