from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import json

import numpy as np

from sklearn.base import clone
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.linear_model import (
    LogisticRegression,
)
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import (
    train_test_split,
)
from sklearn.pipeline import (
    Pipeline,
)
from sklearn.preprocessing import (
    StandardScaler,
)

from bot_engine.datasets.cresci_subset import (
    load_cresci_subset,
)


DATA_ROOT = Path(
    "ml_data/bot_detection/"
    "cresci_subset"
)

OUTPUT_DIR = Path(
    "ml/evaluation/"
    "bot_detection/"
    "cresci_subset"
)

SEEDS = [
    1,
    2,
    3,
    4,
    5,
]


def create_models(
    seed: int,
) -> dict:
    return {
        "logistic_regression":
            Pipeline(
                [
                    (
                        "scaler",
                        StandardScaler(),
                    ),
                    (
                        "model",
                        LogisticRegression(
                            max_iter=3000,
                            class_weight=(
                                "balanced"
                            ),
                            random_state=seed,
                        ),
                    ),
                ]
            ),

        "random_forest":
            RandomForestClassifier(
                n_estimators=400,
                min_samples_leaf=2,
                class_weight=(
                    "balanced_subsample"
                ),
                random_state=seed,
                n_jobs=-1,
            ),

        "hist_gradient_boosting":
            HistGradientBoostingClassifier(
                max_iter=250,
                learning_rate=0.08,
                max_leaf_nodes=31,
                l2_regularization=0.1,
                random_state=seed,
            ),
    }


def split_dataset(
    X,
    y,
    seed: int,
):
    (
        X_train_val,
        X_test,
        y_train_val,
        y_test,
    ) = train_test_split(
        X,
        y,
        test_size=0.20,
        stratify=y,
        random_state=seed,
    )

    (
        X_train,
        X_val,
        y_train,
        y_val,
    ) = train_test_split(
        X_train_val,
        y_train_val,
        test_size=0.25,
        stratify=y_train_val,
        random_state=seed,
    )

    return (
        X_train,
        X_val,
        X_test,
        y_train,
        y_val,
        y_test,
    )


def positive_probability(
    model,
    X,
):
    if hasattr(
        model,
        "predict_proba",
    ):
        return (
            model.predict_proba(
                X
            )[:, 1]
        )

    return None


def metrics(
    model,
    X,
    y,
) -> dict[str, float]:
    prediction = (
        model.predict(
            X
        )
    )

    probability = (
        positive_probability(
            model,
            X,
        )
    )

    result = {
        "accuracy":
            float(
                accuracy_score(
                    y,
                    prediction,
                )
            ),

        "macro_f1":
            float(
                f1_score(
                    y,
                    prediction,
                    average="macro",
                    zero_division=0,
                )
            ),

        "macro_precision":
            float(
                precision_score(
                    y,
                    prediction,
                    average="macro",
                    zero_division=0,
                )
            ),

        "macro_recall":
            float(
                recall_score(
                    y,
                    prediction,
                    average="macro",
                    zero_division=0,
                )
            ),
    }

    if probability is not None:
        result[
            "roc_auc"
        ] = float(
            roc_auc_score(
                y,
                probability,
            )
        )

    return result


def summarize(
    values: list[float],
) -> dict[str, float]:
    array = np.asarray(
        values,
        dtype=float,
    )

    return {
        "mean":
            float(
                array.mean()
            ),
        "std":
            float(
                array.std(
                    ddof=0
                )
            ),
    }


def main() -> None:
    dataset = (
        load_cresci_subset(
            DATA_ROOT
        )
    )

    print("=" * 72)
    print("BOT DETECTION BASELINE")
    print("=" * 72)

    print(
        "Dataset:",
        dataset.dataset_name,
    )

    print(
        "Samples:",
        dataset.sample_count,
    )

    print(
        "Humans:",
        dataset.human_count,
    )

    print(
        "Bots:",
        dataset.bot_count,
    )

    print(
        "Features:",
        dataset.X.shape[1],
    )

    validation_runs: dict[
        str,
        list[float],
    ] = {}

    for seed in SEEDS:
        (
            X_train,
            X_val,
            _,
            y_train,
            y_val,
            _,
        ) = split_dataset(
            dataset.X,
            dataset.y,
            seed,
        )

        models = (
            create_models(
                seed
            )
        )

        print()
        print(
            f"--- Validation seed {seed} ---"
        )

        for (
            name,
            model,
        ) in models.items():
            model.fit(
                X_train,
                y_train,
            )

            score = f1_score(
                y_val,
                model.predict(
                    X_val
                ),
                average="macro",
                zero_division=0,
            )

            validation_runs.setdefault(
                name,
                [],
            ).append(
                float(score)
            )

            print(
                f"{name:24s} "
                f"macro-F1={score:.4f}"
            )

    validation_summary = {
        name:
            summarize(
                scores
            )
        for name, scores
        in validation_runs.items()
    }

    selected_model = max(
        sorted(
            validation_summary
        ),
        key=lambda name:
            validation_summary[
                name
            ]["mean"],
    )

    print()
    print("=" * 72)
    print("VALIDATION SUMMARY")
    print("=" * 72)

    for name in sorted(
        validation_summary
    ):
        summary = (
            validation_summary[
                name
            ]
        )

        print(
            f"{name:24s} "
            f"{summary['mean']:.4f} "
            f"± {summary['std']:.4f}"
        )

    print()
    print(
        "Selected model:",
        selected_model,
    )

    test_runs = []

    print()
    print("=" * 72)
    print("TEST — SELECTED MODEL ONLY")
    print("=" * 72)

    for seed in SEEDS:
        (
            X_train,
            X_val,
            X_test,
            y_train,
            y_val,
            y_test,
        ) = split_dataset(
            dataset.X,
            dataset.y,
            seed,
        )

        X_train_final = (
            np.concatenate(
                [
                    X_train,
                    X_val,
                ],
                axis=0,
            )
        )

        y_train_final = (
            np.concatenate(
                [
                    y_train,
                    y_val,
                ],
                axis=0,
            )
        )

        model = clone(
            create_models(
                seed
            )[
                selected_model
            ]
        )

        model.fit(
            X_train_final,
            y_train_final,
        )

        result = metrics(
            model,
            X_test,
            y_test,
        )

        result[
            "seed"
        ] = seed

        test_runs.append(
            result
        )

        print(
            f"seed={seed} "
            f"acc={result['accuracy']:.4f} "
            f"F1={result['macro_f1']:.4f} "
            f"AUC={result.get('roc_auc', 0):.4f}"
        )

    metric_names = [
        "accuracy",
        "macro_f1",
        "macro_precision",
        "macro_recall",
        "roc_auc",
    ]

    test_summary = {}

    for metric_name in metric_names:
        values = [
            run[metric_name]
            for run in test_runs
            if metric_name
            in run
        ]

        if values:
            test_summary[
                metric_name
            ] = summarize(
                values
            )

    print()
    print("=" * 72)
    print("TEST SUMMARY")
    print("=" * 72)

    for (
        metric_name,
        summary,
    ) in test_summary.items():
        print(
            f"{metric_name:18s} "
            f"{summary['mean']:.4f} "
            f"± {summary['std']:.4f}"
        )

    output = {
        "dataset":
            dataset.dataset_name,

        "samples":
            dataset.sample_count,

        "class_distribution": {
            "human":
                dataset.human_count,
            "bot":
                dataset.bot_count,
        },

        "feature_names":
            dataset.feature_names,

        "seeds":
            SEEDS,

        "selection_metric":
            "validation_macro_f1",

        "validation":
            validation_summary,

        "selected_model":
            selected_model,

        "test_runs":
            test_runs,

        "test_summary":
            test_summary,

        "limitations": [
            (
                "This is a profile-feature "
                "baseline on a Cresci-derived "
                "human/spam subset."
            ),
            (
                "It is not the complete "
                "Cresci-2017 benchmark."
            ),
            (
                "Random stratified splits can "
                "overestimate cross-dataset "
                "generalization."
            ),
            (
                "Deployment on current X data "
                "is cross-domain and requires "
                "separate validation."
            ),
        ],
    }

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path = (
        OUTPUT_DIR
        / "baseline_summary.json"
    )

    output_path.write_text(
        json.dumps(
            output,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print(
        "Saved:",
        output_path,
    )


if __name__ == "__main__":
    main()
