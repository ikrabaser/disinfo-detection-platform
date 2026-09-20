from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from torch_geometric.datasets import UPFD
from torch_geometric.loader import DataLoader
from torch_geometric.nn import (
    GATConv,
    GCNConv,
    SAGEConv,
    global_mean_pool,
)
from torch_geometric.transforms import ToUndirected


LABEL_NAMES = [
    "fake",
    "real",
]


def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


class GraphClassifier(torch.nn.Module):
    def __init__(
        self,
        model_type: str,
        in_channels: int,
        hidden_channels: int = 64,
        out_channels: int = 2,
        dropout: float = 0.3,
    ):
        super().__init__()

        self.model_type = model_type
        self.dropout = dropout

        if model_type == "gcn":
            self.conv1 = GCNConv(
                in_channels,
                hidden_channels,
            )

            self.conv2 = GCNConv(
                hidden_channels,
                hidden_channels,
            )

        elif model_type == "gat":
            self.conv1 = GATConv(
                in_channels,
                hidden_channels,
                heads=2,
                concat=False,
            )

            self.conv2 = GATConv(
                hidden_channels,
                hidden_channels,
                heads=2,
                concat=False,
            )

        elif model_type == "graphsage":
            self.conv1 = SAGEConv(
                in_channels,
                hidden_channels,
            )

            self.conv2 = SAGEConv(
                hidden_channels,
                hidden_channels,
            )

        else:
            raise ValueError(
                f"Desteklenmeyen model: {model_type}"
            )

        self.classifier = torch.nn.Linear(
            hidden_channels,
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

        x = global_mean_pool(
            x,
            batch,
        )

        return self.classifier(x)


def evaluate(
    model,
    loader,
    device,
):
    model.eval()

    labels = []
    predictions = []

    with torch.no_grad():
        for batch in loader:
            batch = batch.to(device)

            logits = model(
                batch.x,
                batch.edge_index,
                batch.batch,
            )

            preds = logits.argmax(
                dim=-1
            )

            labels.extend(
                batch.y.view(-1)
                .cpu()
                .tolist()
            )

            predictions.extend(
                preds.cpu().tolist()
            )

    accuracy = accuracy_score(
        labels,
        predictions,
    )

    precision, recall, f1, _ = (
        precision_recall_fscore_support(
            labels,
            predictions,
            average="macro",
            zero_division=0,
        )
    )

    return {
        "accuracy": float(accuracy),
        "precision_macro": float(precision),
        "recall_macro": float(recall),
        "f1_macro": float(f1),
        "labels": labels,
        "predictions": predictions,
    }


def train_model(
    model_type: str,
    train_loader,
    val_loader,
    test_loader,
    in_channels: int,
    device,
    output_root: Path,
    epochs: int,
):
    print()
    print("=" * 60)
    print(
        f"{model_type.upper()} EĞİTİMİ"
    )
    print("=" * 60)

    model = GraphClassifier(
        model_type=model_type,
        in_channels=in_channels,
    ).to(device)

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=1e-3,
        weight_decay=1e-4,
    )

    criterion = (
        torch.nn.CrossEntropyLoss()
    )

    best_val_f1 = -1.0
    best_state = None

    for epoch in range(
        1,
        epochs + 1,
    ):
        model.train()

        total_loss = 0.0

        for batch in train_loader:
            batch = batch.to(device)

            optimizer.zero_grad()

            logits = model(
                batch.x,
                batch.edge_index,
                batch.batch,
            )

            loss = criterion(
                logits,
                batch.y.view(-1),
            )

            loss.backward()
            optimizer.step()

            total_loss += (
                loss.item()
                * batch.num_graphs
            )

        train_loss = (
            total_loss
            / len(
                train_loader.dataset
            )
        )

        val_metrics = evaluate(
            model,
            val_loader,
            device,
        )

        print(
            f"Epoch {epoch:03d} | "
            f"loss={train_loss:.4f} | "
            f"val_acc={val_metrics['accuracy']:.4f} | "
            f"val_f1={val_metrics['f1_macro']:.4f}"
        )

        if (
            val_metrics["f1_macro"]
            > best_val_f1
        ):
            best_val_f1 = (
                val_metrics[
                    "f1_macro"
                ]
            )

            best_state = {
                key: value
                .detach()
                .cpu()
                .clone()
                for key, value
                in model.state_dict().items()
            }

        


    if best_state is not None:
        model.load_state_dict(
            best_state
        )

    test_metrics = evaluate(
        model,
        test_loader,
        device,
    )

    print()
    print(
        f"{model_type.upper()} TEST"
    )

    print(
        classification_report(
            test_metrics["labels"],
            test_metrics[
                "predictions"
            ],
            labels=[0, 1],
            target_names=LABEL_NAMES,
            zero_division=0,
        )
    )

    matrix = confusion_matrix(
        test_metrics["labels"],
        test_metrics[
            "predictions"
        ],
        labels=[0, 1],
    )

    print("Confusion Matrix:")
    print(matrix)

    output_dir = (
        output_root
        / model_type
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    torch.save(
        {
            "model_type": model_type,
            "in_channels": in_channels,
            "hidden_channels": 64,
            "out_channels": 2,
            "state_dict": model.state_dict(),
            "label_map": {
                "0": "fake",
                "1": "real",
            },
        },
        output_dir
        / "model.pt",
    )

    result = {
        "model": model_type,
        "best_validation_f1": (
            best_val_f1
        ),
        "test_accuracy": (
            test_metrics[
                "accuracy"
            ]
        ),
        "test_precision_macro": (
            test_metrics[
                "precision_macro"
            ]
        ),
        "test_recall_macro": (
            test_metrics[
                "recall_macro"
            ]
        ),
        "test_f1_macro": (
            test_metrics[
                "f1_macro"
            ]
        ),
        "confusion_matrix": (
            matrix.tolist()
        ),
    }

    with (
        output_dir
        / "metrics.json"
    ).open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            result,
            file,
            indent=2,
        )

    return result


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--epochs",
        type=int,
        default=100,
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
    )

    parser.add_argument(
        "--dataset",
        default="politifact",
        choices=[
            "politifact",
            "gossipcop",
        ],
    )

    args = parser.parse_args()

    set_seed(42)

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print(
        "Device:",
        device,
    )

    root = (
        Path("ml_data")
        / "UPFD"
    )

    transform = ToUndirected()

    train_dataset = UPFD(
        root=str(root),
        name=args.dataset,
        feature="profile",
        split="train",
        transform=transform,
    )

    val_dataset = UPFD(
        root=str(root),
        name=args.dataset,
        feature="profile",
        split="val",
        transform=transform,
    )

    test_dataset = UPFD(
        root=str(root),
        name=args.dataset,
        feature="profile",
        split="test",
        transform=transform,
    )

    print()
    print(
        "Train:",
        len(train_dataset),
    )

    print(
        "Validation:",
        len(val_dataset),
    )

    print(
        "Test:",
        len(test_dataset),
    )

    in_channels = (
        train_dataset.num_features
    )

    print(
        "Node features:",
        in_channels,
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=args.batch_size,
        shuffle=True,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=args.batch_size,
        shuffle=False,
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=args.batch_size,
        shuffle=False,
    )

    output_root = (
        Path("ml_models")
        / "upfd"
        / args.dataset
    )

    results = []

    for model_type in [
        "gcn",
        "gat",
        "graphsage",
    ]:
        result = train_model(
            model_type=model_type,
            train_loader=train_loader,
            val_loader=val_loader,
            test_loader=test_loader,
            in_channels=in_channels,
            device=device,
            output_root=output_root,
            epochs=args.epochs,
        )

        results.append(result)

    print()
    print("=" * 60)
    print("MODEL KARŞILAŞTIRMASI")
    print("=" * 60)

    for result in results:
        print(
            f"{result['model']:10s} | "
            f"acc={result['test_accuracy']:.4f} | "
            f"macro_f1={result['test_f1_macro']:.4f}"
        )

    output_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    with (
        output_root
        / "comparison.json"
    ).open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            results,
            file,
            indent=2,
        )


if __name__ == "__main__":
    main()
