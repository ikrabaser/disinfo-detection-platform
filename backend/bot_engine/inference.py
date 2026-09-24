from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
from django.conf import settings

from bot_engine.features import (
    BOT_FEATURE_NAMES,
    extract_bot_feature_batch,
)


MODEL_NAME = (
    "random-forest-cresci-profile"
)

FEATURE_SET = (
    "profile-13d"
)

DEFAULT_CHECKPOINT = (
    Path(settings.BASE_DIR)
    / "ml_models"
    / "bot_detection"
    / "cresci_subset"
    / "random_forest.joblib"
)


class BotInferenceError(
    RuntimeError
):
    pass


@lru_cache(maxsize=1)
def load_bot_model(
    checkpoint_path: str | None = None,
):
    path = (
        Path(checkpoint_path)
        if checkpoint_path
        else DEFAULT_CHECKPOINT
    )

    if not path.exists():
        raise BotInferenceError(
            "Bot model checkpoint "
            f"bulunamadi: {path}"
        )

    payload = joblib.load(
        path
    )

    model = payload.get(
        "model"
    )

    if model is None:
        raise BotInferenceError(
            "Checkpoint icinde "
            "model bulunamadi."
        )

    feature_names = (
        payload.get(
            "feature_names"
        )
    )

    if feature_names != list(
        BOT_FEATURE_NAMES
    ):
        raise BotInferenceError(
            "Bot model feature semasi "
            "uyusmuyor."
        )

    if (
        payload.get(
            "model_type"
        )
        != "random_forest"
    ):
        raise BotInferenceError(
            "Beklenmeyen bot "
            "model tipi."
        )

    return payload


def predict_graph_users(
    nodes: list[dict],
) -> dict:
    batch = (
        extract_bot_feature_batch(
            nodes
        )
    )

    if batch.user_count == 0:
        return {
            "user_count": 0,
            "scores": {},
            "predictions": {},
            "flagged_users": [],
            "model": MODEL_NAME,
            "feature_set":
                FEATURE_SET,
            "training_dataset":
                "cresci-derived-"
                "trustnet-subset",
            "cross_domain": True,
            "score_calibrated":
                False,
        }

    payload = (
        load_bot_model()
    )

    model = payload[
        "model"
    ]

    probabilities = (
        model.predict_proba(
            batch.matrix
        )
    )

    classes = list(
        model.classes_
    )

    try:
        bot_index = (
            classes.index(1)
        )
    except ValueError as exc:
        raise BotInferenceError(
            "Model bot class=1 "
            "icermiyor."
        ) from exc

    bot_scores = (
        probabilities[
            :,
            bot_index
        ]
    )

    predictions: dict[
        str,
        dict,
    ] = {}

    scores: dict[
        str,
        float,
    ] = {}

    flagged_users: list[
        str
    ] = []

    for (
        user_id,
        bot_score,
    ) in zip(
        batch.user_ids,
        bot_scores,
    ):
        bot_score = float(
            bot_score
        )

        human_score = (
            1.0
            - bot_score
        )

        predicted_label = (
            "bot"
            if bot_score >= 0.5
            else "human"
        )

        confidence = max(
            bot_score,
            human_score,
        )

        rounded_score = round(
            bot_score,
            6,
        )

        scores[
            user_id
        ] = rounded_score

        predictions[
            user_id
        ] = {
            "predicted_label":
                predicted_label,

            "bot_score":
                rounded_score,

            "human_score":
                round(
                    human_score,
                    6,
                ),

            "confidence":
                round(
                    confidence,
                    6,
                ),
        }

        if predicted_label == "bot":
            flagged_users.append(
                user_id
            )

    average_score = float(
        np.mean(
            bot_scores
        )
    )

    max_score = float(
        np.max(
            bot_scores
        )
    )

    return {
        "user_count":
            batch.user_count,

        "scores":
            scores,

        "predictions":
            predictions,

        "flagged_users":
            flagged_users,

        "flagged_count":
            len(
                flagged_users
            ),

        "average_bot_score":
            round(
                average_score,
                6,
            ),

        "max_bot_score":
            round(
                max_score,
                6,
            ),

        "model":
            MODEL_NAME,

        "model_type":
            payload[
                "model_type"
            ],

        "feature_set":
            FEATURE_SET,

        "training_dataset":
            payload[
                "dataset"
            ],

        "training_samples":
            payload[
                "sample_count"
            ],

        "cross_domain":
            True,

        "score_calibrated":
            False,

        "note": (
            "Model Cresci-derived "
            "historical Twitter profile "
            "verisi uzerinde egitilmistir. "
            "Guncel X hesaplarina uygulama "
            "cross-domain deneysel bir "
            "model sinyalidir; bot_score "
            "kalibre edilmis olasilik "
            "degildir."
        ),
    }
