from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from bot_engine.features import (
    BOT_FEATURE_NAMES,
    build_bot_feature_vector,
)


DATASET_NAME = "cresci-derived-trustnet-subset"

HUMAN_LABEL = 0
BOT_LABEL = 1


@dataclass(frozen=True)
class BotDataset:
    X: np.ndarray
    y: np.ndarray
    user_ids: list[str]
    feature_names: list[str]
    dataset_name: str

    @property
    def sample_count(self) -> int:
        return len(self.y)

    @property
    def bot_count(self) -> int:
        return int(
            np.sum(
                self.y == BOT_LABEL
            )
        )

    @property
    def human_count(self) -> int:
        return int(
            np.sum(
                self.y == HUMAN_LABEL
            )
        )


def _safe_text(
    value: Any,
) -> str:
    if pd.isna(value):
        return ""

    return str(value).strip()


def _safe_number(
    value: Any,
) -> float:
    if pd.isna(value):
        return 0.0

    try:
        number = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return 0.0

    if not np.isfinite(number):
        return 0.0

    return max(
        0.0,
        number,
    )


def _safe_bool(
    value: Any,
) -> bool:
    if pd.isna(value):
        return False

    if isinstance(
        value,
        bool,
    ):
        return value

    if isinstance(
        value,
        (int, float),
    ):
        return bool(value)

    normalized = (
        str(value)
        .strip()
        .lower()
    )

    return normalized in {
        "1",
        "true",
        "yes",
        "y",
        "t",
    }


def _parse_datetime(
    value: Any,
) -> datetime | None:
    if pd.isna(value):
        return None

    parsed = pd.to_datetime(
        value,
        utc=True,
        errors="coerce",
    )

    if pd.isna(parsed):
        return None

    return parsed.to_pydatetime()


def _resolve_observed_at(
    row: pd.Series,
) -> datetime:
    for column in [
        "crawled_at",
        "updated",
        "timestamp",
    ]:
        parsed = _parse_datetime(
            row.get(column)
        )

        if parsed is not None:
            return parsed

    # Dataset 2016 civarinda derlendigi icin
    # sadece metadata tamamen eksikse deterministik
    # fallback kullanilir.
    return datetime(
        2016,
        1,
        1,
        tzinfo=timezone.utc,
    )


def _row_to_profile(
    row: pd.Series,
) -> dict[str, Any]:
    name = _safe_text(
        row.get("name")
    )

    description = _safe_text(
        row.get("description")
    )

    created_at = _parse_datetime(
        row.get("created_at")
    )

    return {
        "author_id":
            _safe_text(
                row.get("id")
            ),

        "author_username":
            _safe_text(
                row.get(
                    "screen_name"
                )
            ),

        "author_description":
            description,

        "author_created_at":
            (
                created_at.isoformat()
                if created_at
                else None
            ),

        "author_followers_count":
            _safe_number(
                row.get(
                    "followers_count"
                )
            ),

        # Eski Twitter API'deki
        # friends_count =
        # takip edilen hesap sayisi.
        "author_following_count":
            _safe_number(
                row.get(
                    "friends_count"
                )
            ),

        "author_post_count":
            _safe_number(
                row.get(
                    "statuses_count"
                )
            ),

        "author_listed_count":
            _safe_number(
                row.get(
                    "listed_count"
                )
            ),

        "author_name_word_count":
            len(
                name.split()
            ),

        "author_description_word_count":
            len(
                description.split()
            ),

        "author_verified":
            _safe_bool(
                row.get(
                    "verified"
                )
            ),
    }


def _load_group(
    path: Path,
    label: int,
) -> tuple[
    list[np.ndarray],
    list[int],
    list[str],
]:
    frame = pd.read_csv(
        path,
        low_memory=False,
    )

    vectors: list[
        np.ndarray
    ] = []

    labels: list[int] = []

    user_ids: list[str] = []

    seen_ids: set[str] = set()

    for _, row in frame.iterrows():
        user_id = _safe_text(
            row.get("id")
        )

        if not user_id:
            continue

        if user_id in seen_ids:
            continue

        seen_ids.add(
            user_id
        )

        profile = (
            _row_to_profile(
                row
            )
        )

        observed_at = (
            _resolve_observed_at(
                row
            )
        )

        vector = (
            build_bot_feature_vector(
                profile,
                observed_at,
            )
        )

        vectors.append(
            vector
        )

        labels.append(
            label
        )

        user_ids.append(
            user_id
        )

    return (
        vectors,
        labels,
        user_ids,
    )


def load_cresci_subset(
    root: str | Path,
) -> BotDataset:
    root = Path(root)

    genuine_path = (
        root
        / "genuine_users.csv"
    )

    spam_path = (
        root
        / "spam_users.csv"
    )

    if not genuine_path.exists():
        raise FileNotFoundError(
            genuine_path
        )

    if not spam_path.exists():
        raise FileNotFoundError(
            spam_path
        )

    (
        human_vectors,
        human_labels,
        human_ids,
    ) = _load_group(
        genuine_path,
        HUMAN_LABEL,
    )

    (
        bot_vectors,
        bot_labels,
        bot_ids,
    ) = _load_group(
        spam_path,
        BOT_LABEL,
    )

    overlap = (
        set(human_ids)
        & set(bot_ids)
    )

    if overlap:
        raise ValueError(
            "Human ve bot dosyalarinda "
            "ayni user ID bulundu: "
            f"{len(overlap)}"
        )

    vectors = (
        human_vectors
        + bot_vectors
    )

    labels = (
        human_labels
        + bot_labels
    )

    user_ids = (
        human_ids
        + bot_ids
    )

    if not vectors:
        raise ValueError(
            "Dataset bos."
        )

    X = np.stack(
        vectors,
        axis=0,
    ).astype(
        np.float32
    )

    y = np.asarray(
        labels,
        dtype=np.int64,
    )

    if not np.isfinite(X).all():
        raise ValueError(
            "Feature matrisinde "
            "NaN/inf bulundu."
        )

    return BotDataset(
        X=X,
        y=y,
        user_ids=user_ids,
        feature_names=list(
            BOT_FEATURE_NAMES
        ),
        dataset_name=(
            DATASET_NAME
        ),
    )
