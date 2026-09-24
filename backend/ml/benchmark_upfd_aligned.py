from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import torch
from torch_geometric.datasets import UPFD
from torch_geometric.loader import DataLoader

from graph_engine.aligned_features import (
    AlignedProfileStructuralTransform,
)
from train_upfd_gnn import (
    set_seed,
    train_model,
)


MODELS = [
    "gcn",
    "gat",
    "graphsage",
]


def make_loaders(
    train_dataset,
    val_dataset,
    test_dataset,
    batch_size: int,
    seed: int,
):
    generator = torch.Generator()
    generator.manual_seed(seed)

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        generator=generator,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
    )

    return (
        train_loader,
        val_loader,
        test_loader,
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--epochs",
        type=int,
        default=50,
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

    parser.add_argument(
        "--seeds",
        type=int,
        nargs="+",
        default=[1, 2, 3, 4, 5],
    )

    args = parser.parse_args()

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print("Device:", device)
    print("Feature mode: aligned-profile+structural")
    print("Seeds:", args.seeds)

    root = (
        Path("ml_data")
        / "UPFD"
    )

    transform = AlignedProfileStructuralTransform()

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

    in_channels = (
        train_dataset[0].num_node_features
    )

    print("Node features:", in_channels)

    results = {
        model: []
        for model in MODELS
    }

    for seed in args.seeds:
        print()
        print("#" * 60)
        print(f"SEED = {seed}")
        print("#" * 60)

        for model_type in MODELS:
            set_seed(seed)

            (
                train_loader,
                val_loader,
                test_loader,
            ) = make_loaders(
                train_dataset,
                val_dataset,
                test_dataset,
                args.batch_size,
                seed,
            )

            output_root = (
                Path("ml_models")
                / "upfd_aligned"
                / args.dataset
                / f"seed_{seed}"
            )

            result = train_model(
                model_type=model_type,
                train_loader=train_loader,
                val_loader=val_loader,
                test_loader=test_loader,
                in_channels=in_channels,
                device=device,
                output_root=output_root,
                epochs=args.epochs,
                pooling="multi",
            )

            result["seed"] = seed

            results[
                model_type
            ].append(result)

    summary = {}

    print()
    print("=" * 70)
    print("ALIGNED PROFILE + STRUCTURAL SONUÇLARI")
    print("=" * 70)

    for model_type in MODELS:
        runs = results[model_type]

        accuracies = [
            run["test_accuracy"]
            for run in runs
        ]

        f1_scores = [
            run["test_f1_macro"]
            for run in runs
        ]

        accuracy_mean = statistics.mean(
            accuracies
        )

        accuracy_std = (
            statistics.stdev(accuracies)
            if len(accuracies) > 1
            else 0.0
        )

        f1_mean = statistics.mean(
            f1_scores
        )

        f1_std = (
            statistics.stdev(f1_scores)
            if len(f1_scores) > 1
            else 0.0
        )

        summary[model_type] = {
            "accuracy_mean": accuracy_mean,
            "accuracy_std": accuracy_std,
            "f1_macro_mean": f1_mean,
            "f1_macro_std": f1_std,
            "runs": runs,
        }

        print(
            f"{model_type:10s} | "
            f"accuracy="
            f"{accuracy_mean:.4f} "
            f"± {accuracy_std:.4f} | "
            f"macro_f1="
            f"{f1_mean:.4f} "
            f"± {f1_std:.4f}"
        )

    evaluation_dir = (
        Path("ml")
        / "evaluation"
        / "upfd"
        / args.dataset
    )

    evaluation_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        evaluation_dir
        / "aligned_multi_seed_summary.json"
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            summary,
            file,
            indent=2,
        )

    print()
    print(
        "Sonuç kaydedildi:",
        output_file,
    )


if __name__ == "__main__":
    main()
