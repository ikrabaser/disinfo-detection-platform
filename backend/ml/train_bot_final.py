from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
from sklearn.ensemble import (
    RandomForestClassifier,
)

BACKEND_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND_ROOT),
    )

from bot_engine.datasets.cresci_subset import (
    load_cresci_subset,
)


DATA_ROOT = Path(
    "ml_data/bot_detection/"
    "cresci_subset"
)

MODEL_DIR = Path(
    "ml_models/"
    "bot_detection/"
    "cresci_subset"
)

MODEL_PATH = (
    MODEL_DIR
    / "random_forest.joblib"
)

METADATA_PATH = (
    MODEL_DIR
    / "metadata.json"
)

RANDOM_STATE = 42


def main() -> None:
    dataset = (
        load_cresci_subset(
            DATA_ROOT
        )
    )

    print("=" * 72)
    print("FINAL BOT MODEL TRAINING")
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

    model = (
        RandomForestClassifier(
            n_estimators=400,
            min_samples_leaf=2,
            class_weight=(
                "balanced_subsample"
            ),
            random_state=(
                RANDOM_STATE
            ),
            n_jobs=-1,
        )
    )

    model.fit(
        dataset.X,
        dataset.y,
    )

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "model":
            model,

        "model_type":
            "random_forest",

        "dataset":
            dataset.dataset_name,

        "feature_names":
            dataset.feature_names,

        "sample_count":
            dataset.sample_count,

        "human_count":
            dataset.human_count,

        "bot_count":
            dataset.bot_count,

        "random_state":
            RANDOM_STATE,

        "score_calibrated":
            False,
    }

    joblib.dump(
        payload,
        MODEL_PATH,
    )

    feature_importance = {
        feature_name:
            float(importance)
        for (
            feature_name,
            importance,
        )
        in zip(
            dataset.feature_names,
            model.feature_importances_,
        )
    }

    feature_importance = dict(
        sorted(
            feature_importance.items(),
            key=lambda item:
                item[1],
            reverse=True,
        )
    )

    metadata = {
        key: value
        for key, value
        in payload.items()
        if key != "model"
    }

    metadata[
        "feature_importance"
    ] = feature_importance

    METADATA_PATH.write_text(
        json.dumps(
            metadata,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print(
        "Model saved:",
        MODEL_PATH,
    )

    print(
        "Metadata saved:",
        METADATA_PATH,
    )

    print()
    print("Feature importance:")

    for (
        feature,
        importance,
    ) in feature_importance.items():
        print(
            f"{feature:32s} "
            f"{importance:.4f}"
        )


if __name__ == "__main__":
    main()
